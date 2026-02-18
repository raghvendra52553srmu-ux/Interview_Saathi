import os
import json
import tempfile
import random  # <--- NEW: Import random to pick questions
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# from whisper_logic import transcribe_audio
from groq_logic import analyze_interview_response, generate_interview_question

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"])

# ─────────────────────────────────────────────
# 1. NEW: Static English Question Database
# ─────────────────────────────────────────────
QUESTIONS_DB = {
    "Software Engineer": [
        "Can you explain the difference between a process and a thread?",
        "Describe a time you fixed a critical bug in production. How did you handle it?",
        "What is your preferred programming language and why?",
        "Explain the concept of OOPs (Object Oriented Programming) with real-life examples.",
        "How do you handle merge conflicts in Git?",
        "Tell me about a challenging project you worked on."
    ],
    "HR Interview": [
        "Tell me about yourself.",
        "Why do you want to work for this company?",
        "What are your greatest strengths and weaknesses?",
        "Where do you see yourself in five years?",
        "Describe a situation where you had a conflict with a coworker and how you resolved it."
    ],
    "MBA Interview": [
        "Why do you want to pursue an MBA?",
        "Tell me about a time you led a team under pressure.",
        "What are your short-term and long-term career goals?",
        "How do you handle failure?",
        "Describe a situation where you had to make a difficult decision."
    ]
}

# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Interview Saathi backend running!"})


# ─────────────────────────────────────────────
# 2. UPDATED: Generate interview question (Hybrid)
# ─────────────────────────────────────────────
@app.route("/api/question", methods=["POST"])
def get_question():
    """
    Expects: { "role": "Software Engineer" | "HR Interview" | "MBA Interview", "use_ai": false }
    Returns: { "question": "..." }
    """
    data = request.get_json()
    if not data or "role" not in data:
        return jsonify({"error": "Missing 'role' in request body"}), 400

    role = data["role"]
    use_ai = data.get("use_ai", False) # Option to force AI or use static list

    try:
        # Option A: Use AI Generation (if requested)
        if use_ai:
            question = generate_interview_question(role)
        
        # Option B: Use Static List (Faster & Reliable English)
        else:
            # Get list for role, or default to HR questions if role not found
            question_list = QUESTIONS_DB.get(role, QUESTIONS_DB["HR Interview"])
            question = random.choice(question_list)

        return jsonify({"question": question})

    except Exception as e:
        # Fallback: If AI fails, return a static question
        fallback_q = random.choice(QUESTIONS_DB.get("HR Interview"))
        return jsonify({"question": fallback_q, "note": "Served from backup"}), 200

# ─────────────────────────────────────────────
# Transcribe audio + Analyze response (UNCHANGED)
# ─────────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
def analyze():
    # ... (Keep your existing analyze code exactly the same) ...
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    role = request.form.get("role", "Software Engineer")
    question = request.form.get("question", "Tell me about yourself.")
    audio_file = request.files["audio"]

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # NOTE: Using your debug transcript for now
        transcript = "This is a temporary test answer for debugging." 
        
        # Uncomment this when whisper_logic is ready:
        # transcript = transcribe_audio(tmp_path)

        analysis = analyze_interview_response(transcript, role, question)

        # Score calculation logic
        grammar = analysis.get("grammar_score", 5)
        structure = analysis.get("structure_score", 5)
        tone = analysis.get("professional_tone_score", 5)
        filler_count = len(analysis.get("filler_words", []))
        confidence = min(10, max(0, 10 - (filler_count * 1.5)))

        readiness_score = round(((grammar * 0.3) + (structure * 0.3) + (tone * 0.2) + (confidence * 0.2)) * 10, 1)

        response = {
            "transcript": transcript,
            "grammar_score": grammar,
            "structure_score": structure,
            "professional_tone_score": tone,
            "confidence_score": round(confidence, 1),
            "filler_words": analysis.get("filler_words", []),
            "star_method_detected": analysis.get("star_method_detected", False),
            "improvement_suggestions": analysis.get("improvement_suggestions", []),
            "rewritten_professional_answer": analysis.get("rewritten_professional_answer", ""),
            "readiness_score": readiness_score,
            "xp_earned": 50
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    print(" Interview Saathi backend starting on http://localhost:5000")
    app.run(debug=True, port=5000, host="0.0.0.0")
