"""Flask app: upload 9th grade homework (PDF/image), get Socratic hints."""
from __future__ import annotations

import os
import uuid

from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from teaching_agent.classify import classify_subject
from teaching_agent.english_tutor import generate_english_hints
from teaching_agent.extraction import extract_text
from teaching_agent.math_tutor import generate_math_hints
from teaching_agent.parsing import split_questions

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp", "bmp", "tiff"}

# In-memory store of generated hint sessions, keyed by a random id. This is
# an MVP single-process app: results live only as long as the server runs.
SESSIONS: dict[str, list[dict]] = {}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    pasted_text = (request.form.get("homework_text") or "").strip()
    raw_text = ""

    uploaded = request.files.get("homework_file")
    if uploaded and uploaded.filename:
        if not _allowed(uploaded.filename):
            return render_template(
                "index.html",
                error="Please upload a PDF or image file (png, jpg, jpeg, webp, bmp, tiff).",
            )
        filename = secure_filename(uploaded.filename)
        temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{filename}")
        uploaded.save(temp_path)
        try:
            raw_text = extract_text(temp_path, filename)
        finally:
            os.remove(temp_path)

    combined_text = "\n".join(t for t in [raw_text, pasted_text] if t).strip()

    if not combined_text:
        return render_template(
            "index.html",
            error="We couldn't find any text in that file. Try a clearer photo/PDF, "
                  "or paste the homework text below instead.",
        )

    questions = split_questions(combined_text)
    results = []
    for question in questions:
        subject = classify_subject(question)
        guidance = generate_math_hints(question) if subject == "math" else generate_english_hints(question)
        results.append({
            "question": question,
            "subject": subject,
            "topic_label": guidance.topic_label,
            "hints": [{"text": step.text, "is_answer": step.is_answer} for step in guidance.steps],
        })

    session_id = uuid.uuid4().hex
    SESSIONS[session_id] = results
    return redirect(url_for("results", session_id=session_id))


@app.route("/results/<session_id>")
def results(session_id):
    data = SESSIONS.get(session_id)
    if data is None:
        abort(404)
    return render_template("results.html", questions=data)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
