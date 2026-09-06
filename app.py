import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# Initialize Groq client using environment variable
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


@app.route("/api/config", methods=["GET"])
def get_config():
  # Tells frontend if backend has the API key configured
  return jsonify({"has_key": api_key is not None})


@app.route("/chat", methods=["POST"])
def chat():
  if not client:
    return jsonify({"error": "GROQ_API_KEY is not configured on server"}), 500

  data = request.json
  user_message = data.get("message", "")

  try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": user_message}],
        model="llama-3.3-70b-versatile",
    )
    bot_reply = response.choices[0].message.content
    return jsonify({"reply": bot_reply})
  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  app.run()
