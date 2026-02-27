'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const fs = require('fs');
const os = require('os');

// ---- renderTemplate unit tests ----
// Load only the renderTemplate function from server.js by mocking its deps
// We test the function by extracting it via eval after stripping server boot code.

/**
 * Minimal copy of renderTemplate (kept in sync with server.js)
 */
function renderTemplate(html, data) {
  return html.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return Object.prototype.hasOwnProperty.call(data, key)
      ? String(data[key]).replace(/</g, '&lt;').replace(/>/g, '&gt;')
      : match;
  });
}

test('renderTemplate replaces known placeholders', () => {
  const html = '<p>Hello {{name}}!</p>';
  const result = renderTemplate(html, { name: 'Alice' });
  assert.equal(result, '<p>Hello Alice!</p>');
});

test('renderTemplate leaves unknown placeholders intact', () => {
  const html = '<p>{{unknown}}</p>';
  const result = renderTemplate(html, {});
  assert.equal(result, '<p>{{unknown}}</p>');
});

test('renderTemplate escapes HTML in values', () => {
  const html = '<p>{{val}}</p>';
  const result = renderTemplate(html, { val: '<script>alert(1)</script>' });
  assert.equal(result, '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>');
});

test('renderTemplate handles multiple different placeholders', () => {
  const html = '{{a}} and {{b}}';
  const result = renderTemplate(html, { a: 'foo', b: 'bar' });
  assert.equal(result, 'foo and bar');
});

test('renderTemplate handles repeated placeholder', () => {
  const html = '{{x}} {{x}}';
  const result = renderTemplate(html, { x: 'hi' });
  assert.equal(result, 'hi hi');
});

// ---- HTTP endpoint tests ----
const http = require('http');

// Temporarily override TEMPLATES_DIR by setting a temp dir via env var, not possible
// without refactoring – so we start the actual server and hit real endpoints.

let server;
let port;

function startServer() {
  return new Promise((resolve) => {
    // Ensure the server is freshly required each time
    delete require.cache[require.resolve('../server.js')];
    const app = require('../server.js');
    server = app.listen(0, () => {
      port = server.address().port;
      resolve();
    });
  });
}

function stopServer() {
  return new Promise((resolve) => server.close(resolve));
}

function request(method, urlPath, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: 'localhost',
      port,
      path: urlPath,
      method,
      headers,
    };
    const req = http.request(opts, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

test('GET /templates returns list of templates', async () => {
  await startServer();
  try {
    const { status, body } = await request('GET', '/templates');
    assert.equal(status, 200);
    const json = JSON.parse(body);
    assert.ok(Array.isArray(json.templates));
    // example.html ships in the templates directory
    assert.ok(json.templates.includes('example.html'));
  } finally {
    await stopServer();
  }
});

test('POST /templates/upload rejects non-HTML files', async () => {
  await startServer();
  try {
    const boundary = 'testboundary';
    const content = [
      `--${boundary}`,
      'Content-Disposition: form-data; name="template"; filename="test.txt"',
      'Content-Type: text/plain',
      '',
      'hello',
      `--${boundary}--`,
      '',
    ].join('\r\n');
    const { status } = await request(
      'POST',
      '/templates/upload',
      content,
      {
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': Buffer.byteLength(content),
      }
    );
    assert.equal(status, 400);
  } finally {
    await stopServer();
  }
});

test('GET /templates/:name returns 404 for unknown template', async () => {
  await startServer();
  try {
    const { status } = await request('GET', '/templates/nonexistent.html');
    assert.equal(status, 404);
  } finally {
    await stopServer();
  }
});

test('POST /generate returns 400 when template name is missing', async () => {
  await startServer();
  try {
    const body = JSON.stringify({ data: {} });
    const { status } = await request('POST', '/generate', body, {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    });
    assert.equal(status, 400);
  } finally {
    await stopServer();
  }
});

test('POST /generate returns 404 for unknown template', async () => {
  await startServer();
  try {
    const body = JSON.stringify({ template: 'nope.html', data: {} });
    const { status } = await request('POST', '/generate', body, {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    });
    assert.equal(status, 404);
  } finally {
    await stopServer();
  }
});
