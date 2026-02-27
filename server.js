'use strict';

const express = require('express');
const multer = require('multer');
const puppeteer = require('puppeteer-core');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

const TEMPLATES_DIR = path.join(__dirname, 'templates');
const GENERATED_DIR = path.join(__dirname, 'generated');

// Ensure directories exist
[TEMPLATES_DIR, GENERATED_DIR].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Configure multer for template uploads (HTML files only, 5 MB limit)
const storage = multer.diskStorage({
  destination: TEMPLATES_DIR,
  filename: (req, file, cb) => {
    const safeName = path.basename(file.originalname).replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, safeName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'text/html' || file.originalname.endsWith('.html')) {
      cb(null, true);
    } else {
      cb(new Error('Only HTML template files are supported'));
    }
  },
});

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Rate limiter: 60 requests per minute for general API routes
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
});

// Stricter rate limiter for PDF generation (CPU/memory intensive)
const generateLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/templates', apiLimiter);
app.use('/generate', generateLimiter);

// List all uploaded templates
app.get('/templates', (req, res) => {
  const files = fs.readdirSync(TEMPLATES_DIR).filter((f) => f.endsWith('.html'));
  res.json({ templates: files });
});

// Upload a template
app.post('/templates/upload', (req, res) => {
  upload.single('template')(req, res, (err) => {
    if (err) {
      return res.status(400).json({ error: err.message });
    }
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }
    res.json({ message: 'Template uploaded successfully', filename: req.file.filename });
  });
});

// Delete a template
app.delete('/templates/:name', (req, res) => {
  const name = path.basename(req.params.name);
  const filePath = path.join(TEMPLATES_DIR, name);
  if (!filePath.startsWith(TEMPLATES_DIR + path.sep) && filePath !== TEMPLATES_DIR) {
    return res.status(400).json({ error: 'Invalid template name' });
  }
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'Template not found' });
  }
  fs.unlinkSync(filePath);
  res.json({ message: 'Template deleted' });
});

// Get template content
app.get('/templates/:name', (req, res) => {
  const name = path.basename(req.params.name);
  const filePath = path.join(TEMPLATES_DIR, name);
  if (!filePath.startsWith(TEMPLATES_DIR + path.sep) && filePath !== TEMPLATES_DIR) {
    return res.status(400).json({ error: 'Invalid template name' });
  }
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'Template not found' });
  }
  res.sendFile(filePath);
});

const CHROMIUM_CANDIDATES = [
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/usr/bin/google-chrome',
];

function findChromiumPath() {
  if (process.env.CHROMIUM_PATH) return process.env.CHROMIUM_PATH;
  return CHROMIUM_CANDIDATES.find((p) => fs.existsSync(p));
}

/**
 * @param {string} html - HTML template content
 * @param {Object} data - key/value pairs to substitute
 * @returns {string} rendered HTML
 */
function renderTemplate(html, data) {
  return html.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return Object.prototype.hasOwnProperty.call(data, key)
      ? String(data[key]).replace(/</g, '&lt;').replace(/>/g, '&gt;')
      : match;
  });
}

// Generate PDF from a template with provided data
app.post('/generate', async (req, res) => {
  const { template, data = {} } = req.body;
  if (!template) {
    return res.status(400).json({ error: 'template name is required' });
  }

  const templateName = path.basename(template);
  const templatePath = path.join(TEMPLATES_DIR, templateName);
  if (!templatePath.startsWith(TEMPLATES_DIR + path.sep) && templatePath !== TEMPLATES_DIR) {
    return res.status(400).json({ error: 'Invalid template name' });
  }
  if (!fs.existsSync(templatePath)) {
    return res.status(404).json({ error: 'Template not found' });
  }

  const html = fs.readFileSync(templatePath, 'utf8');
  const rendered = renderTemplate(html, data);

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath: findChromiumPath(),
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      headless: true,
    });
    const page = await browser.newPage();
    await page.setContent(rendered, { waitUntil: 'networkidle0' });
    const pdfBuffer = await page.pdf({ format: 'A4', printBackground: true });

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="${templateName.replace(/\.html$/, '')}.pdf"`
    );
    res.send(Buffer.from(pdfBuffer));
  } catch (err) {
    res.status(500).json({ error: 'PDF generation failed', details: err.message });
  } finally {
    if (browser) {
      await browser.close();
    }
  }
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`PDF Generator server running at http://localhost:${PORT}`);
  });
}

module.exports = app;
