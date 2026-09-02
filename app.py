from flask import Flask, render_template, request, jsonify, session
import json
import os
import re
import ollama

app = Flask(__name__)

app.secret_key = "uniassist-secret-key"


# =========================================================
# COURSES
# =========================================================

COURSES = [
    "AI & Machine Learning",
    "Data Science",
    "Python Programming",
    "Web Development"
]


# =========================================================
# AI INSTRUCTIONS
# =========================================================

AI_INSTRUCTIONS = """
You are UniAssist AI, a friendly student registration and
internship assistant.

You help students with:

- Courses
- Data Science
- Artificial Intelligence
- Machine Learning
- Python
- Web Development
- Eligibility
- Required documents
- Internship information
- Registration guidance
- General educational questions

Behave like a helpful conversational AI.

IMPORTANT:

1. Understand the complete question.
2. Answer naturally and clearly.
3. Do not respond only to keywords.
4. If the user asks about courses, explain the available courses.
5. If the user asks about Data Science, explain Data Science.
6. If the user asks about AI, explain Artificial Intelligence.
7. If the user asks about Python, explain Python.
8. If the user asks about Web Development, explain Web Development.
9. Keep answers beginner-friendly.
10. Use emojis when appropriate.
11. Do not pretend registration has been completed.
12. Do not collect registration information unless registration
    has explicitly been started.

Available courses:

- AI & Machine Learning
- Data Science
- Python Programming
- Web Development
"""


# =========================================================
# FILE LOCATIONS
# =========================================================

REGISTRATION_FILE = "data/registrations.json"

CHAT_HISTORY_FILE = "data/chat_history.json"


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    registrations = load_registrations()

    return render_template(
        "index.html",
        total_students=len(registrations),
        total_courses=len(COURSES),
        total_registrations=len(registrations)
    )


# =========================================================
# REGISTRATION PAGE
# =========================================================

@app.route("/registrations")
def registrations():

    registrations = load_registrations()

    return render_template(
        "registrations.html",
        registrations=registrations
    )


# =========================================================
# CHAT HISTORY PAGE
# =========================================================

@app.route("/history")
def history():

    chat_history = load_chat_history()

    return render_template(
        "history.html",
        history=chat_history
    )


# =========================================================
# RESET SESSION
# =========================================================

@app.route("/reset")
def reset():

    session.clear()

    return """
    <h2>🔄 Session reset successfully.</h2>

    <p>You can return to UniAssist AI.</p>

    <a href="/">Go to UniAssist AI</a>
    """


# =========================================================
# LOAD REGISTRATIONS
# =========================================================

def load_registrations():

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(REGISTRATION_FILE):

        return []

    try:

        with open(REGISTRATION_FILE, "r") as file:

            registrations = json.load(file)

            if isinstance(registrations, list):

                return registrations

    except Exception as error:

        print("REGISTRATION FILE ERROR:", error)

    return []


# =========================================================
# SAVE REGISTRATION
# =========================================================

def save_registration():

    os.makedirs("data", exist_ok=True)

    registrations = load_registrations()

    registration = {
        "name": session.get("name"),
        "email": session.get("email"),
        "phone": session.get("phone"),
        "college": session.get("college"),
        "course": session.get("course")
    }

    registrations.append(registration)

    with open(REGISTRATION_FILE, "w") as file:

        json.dump(
            registrations,
            file,
            indent=4
        )


# =========================================================
# LOAD CHAT HISTORY
# =========================================================

def load_chat_history():

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(CHAT_HISTORY_FILE):

        return []

    try:

        with open(CHAT_HISTORY_FILE, "r") as file:

            history = json.load(file)

            if isinstance(history, list):

                return history

    except Exception as error:

        print("CHAT HISTORY FILE ERROR:", error)

    return []


# =========================================================
# SAVE CHAT MESSAGE
# =========================================================

def save_chat_message(role, message):

    os.makedirs("data", exist_ok=True)

    history = load_chat_history()

    history.append({
        "role": role,
        "message": message
    })

    with open(CHAT_HISTORY_FILE, "w") as file:

        json.dump(
            history,
            file,
            indent=4
        )


# =========================================================
# COURSE DETECTION
# =========================================================

def detect_course(message):

    text = message.lower().strip()

    if "data science" in text:

        return "Data Science"

    if "python" in text:

        return "Python Programming"

    if (
        "machine learning" in text
        or "artificial intelligence" in text
        or text == "ai"
    ):

        return "AI & Machine Learning"

    if "web development" in text:

        return "Web Development"

    return None


# =========================================================
# EMAIL VALIDATION
# =========================================================

def valid_email(email):

    pattern = (
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}$"
    )

    return re.match(pattern, email) is not None


# =========================================================
# PHONE VALIDATION
# =========================================================

def valid_phone(phone):

    digits = re.sub(
        r"\D",
        "",
        phone
    )

    return len(digits) >= 10


# =========================================================
# LOCAL AI
# =========================================================

def get_ai_response(message):

    try:

        old_history = load_chat_history()

        recent_history = old_history[-12:]

        messages = [
            {
                "role": "system",
                "content": AI_INSTRUCTIONS
            }
        ]

        for item in recent_history:

            role = item.get("role")

            content = item.get("message")

            if role in ["user", "assistant"]:

                messages.append({
                    "role": role,
                    "content": content
                })

        messages.append({
            "role": "user",
            "content": message
        })

        response = ollama.chat(
            model="llama3.2",
            messages=messages
        )

        answer = response["message"]["content"]

        return answer

    except Exception as error:

        print("OLLAMA ERROR:", error)

        return (
            "⚠️ <b>I'm having trouble connecting to my "
            "local AI model.</b>"
            "<br><br>"
            "Please make sure Ollama is running."
        )


# =========================================================
# CHAT
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data:

        return jsonify({
            "response": "🤖 I didn't receive your message."
        })


    message = data.get(
        "message",
        ""
    ).strip()


    if not message:

        return jsonify({
            "response": "😊 Please type something."
        })


    text = message.lower().strip()


    # =====================================================
    # CANCEL REGISTRATION
    # =====================================================

    if text in [
        "cancel",
        "cancel registration",
        "stop registration",
        "stop"
    ]:

        session.pop(
            "registration_step",
            None
        )

        save_chat_message(
            "user",
            message
        )

        response_text = (
            "❌ <b>Registration cancelled.</b>"
            "<br><br>"
            "You can continue chatting with me normally."
            "<br><br>"
            "If you want to register later, say "
            "<b>I want to register</b>."
        )

        save_chat_message(
            "assistant",
            response_text
        )

        return jsonify({
            "response": response_text
        })


    # =====================================================
    # START REGISTRATION
    # =====================================================

    if (
        text == "register"
        or text == "registration"
        or text == "registration guide"
        or "i want to register" in text
        or "start registration" in text
    ):

        session.pop("name", None)
        session.pop("email", None)
        session.pop("phone", None)
        session.pop("college", None)
        session.pop("course", None)

        session["registration_step"] = "name"


        save_chat_message(
            "user",
            message
        )


        response_text = (
            "📝 <b>Let's start your registration!</b>"
            "<br><br>"
            "What is your full name?"
        )


        save_chat_message(
            "assistant",
            response_text
        )


        return jsonify({
            "response": response_text
        })


    registration_step = session.get(
        "registration_step"
    )


    # =====================================================
    # NAME
    # =====================================================

    if registration_step == "name":

        course = detect_course(message)

        if course:

            response_text = (
                "😊 First I need your <b>full name</b>."
                "<br><br>"
                "Example: <b>Rahul Kumar</b>"
            )

            save_chat_message(
                "user",
                message
            )

            save_chat_message(
                "assistant",
                response_text
            )

            return jsonify({
                "response": response_text
            })


        if len(message) < 2:

            response_text = (
                "😊 Please enter your full name."
            )

            save_chat_message(
                "user",
                message
            )

            save_chat_message(
                "assistant",
                response_text
            )

            return jsonify({
                "response": response_text
            })


        session["name"] = message

        session["registration_step"] = "email"


        response_text = (
            f"Nice to meet you, <b>{message}</b>! 😊"
            "<br><br>"
            "What is your email address?"
        )


        save_chat_message(
            "user",
            message
        )

        save_chat_message(
            "assistant",
            response_text
        )


        return jsonify({
            "response": response_text
        })


    # =====================================================
    # EMAIL
    # =====================================================

    if registration_step == "email":

        if not valid_email(message):

            response_text = (
                "📧 <b>Please enter a valid email address.</b>"
                "<br><br>"
                "Example: <b>student@gmail.com</b>"
            )

            save_chat_message(
                "user",
                message
            )

            save_chat_message(
                "assistant",
                response_text
            )

            return jsonify({
                "response": response_text
            })


        session["email"] = message

        session["registration_step"] = "phone"


        response_text = (
            "📧 <b>Email saved!</b>"
            "<br><br>"
            "Now please enter your phone number."
        )


        save_chat_message(
            "user",
            message
        )

        save_chat_message(
            "assistant",
            response_text
        )


        return jsonify({
            "response": response_text
        })


    # =====================================================
    # PHONE
    # =====================================================

    if registration_step == "phone":

        if not valid_phone(message):

            response_text = (
                "📱 <b>Please enter a valid phone number.</b>"
                "<br><br>"
                "Example: <b>9876543210</b>"
            )

            save_chat_message(
                "user",
                message
            )

            save_chat_message(
                "assistant",
                response_text
            )

            return jsonify({
                "response": response_text
            })


        phone = re.sub(
            r"\D",
            "",
            message
        )

        session["phone"] = phone

        session["registration_step"] = "college"


        response_text = (
            "📱 <b>Phone number saved!</b>"
            "<br><br>"
            "What is the name of your college?"
        )


        save_chat_message(
            "user",
            message
        )

        save_chat_message(
            "assistant",
            response_text
        )


        return jsonify({
            "response": response_text
        })


    # =====================================================
    # COLLEGE
    # =====================================================

    if registration_step == "college":

        if len(message) < 2:

            response_text = (
                "🎓 Please enter your college name."
            )

            save_chat_message(
                "user",
                message
            )

            save_chat_message(
                "assistant",
                response_text
            )

            return jsonify({
                "response": response_text
            })


        session["college"] = message

        session["registration_step"] = "course"


        response_text = (
            "🎓 <b>Great!</b>"
            "<br><br>"
            "Which course are you interested in?"
            "<br><br>"
            "🤖 AI & Machine Learning"
            "<br>"
            "📊 Data Science"
            "<br>"
            "🐍 Python Programming"
            "<br>"
            "🌐 Web Development"
            "<br><br>"
            "Please type the course name."
        )


        save_chat_message(
            "user",
            message
        )

        save_chat_message(
            "assistant",
            response_text
        )


        return jsonify({
            "response": response_text
        })


    # =====================================================
    # COURSE
    # =====================================================

    if registration_step == "course":

        selected_course = detect_course(
            message
        )


        if selected_course is None:

            response_text = (
                "🎓 <b>Please choose one of these courses:</b>"
                "<br><br>"
                "🤖 AI & Machine Learning"
                "<br>"
                "📊 Data Science"
                "<br>"
                "🐍 Python Programming"
                "<br>"
                "🌐 Web Development"
                "<br><br>"
                "Example: <b>Data Science</b>"
            )


            save_chat_message(
                "user",
                message
            )

            save_chat_message(
                "assistant",
                response_text
            )


            return jsonify({
                "response": response_text
            })


        session["course"] = selected_course

        save_registration()


        name = session.get("name")
        email = session.get("email")
        phone = session.get("phone")
        college = session.get("college")


        session["registration_step"] = "completed"


        response_text = (
            "🎉 <b>REGISTRATION SUCCESSFUL!</b>"
            "<br><br>"
            "Thank you for registering with "
            "<b>UniAssist AI</b>! 🤖"
            "<br><br>"
            f"👤 <b>Name:</b> {name}"
            "<br>"
            f"📧 <b>Email:</b> {email}"
            "<br>"
            f"📱 <b>Phone:</b> {phone}"
            "<br>"
            f"🎓 <b>College:</b> {college}"
            "<br>"
            f"📚 <b>Course:</b> {selected_course}"
            "<br><br>"
            "✅ <b>Your registration has been saved "
            "successfully.</b>"
        )


        save_chat_message(
            "user",
            message
        )

        save_chat_message(
            "assistant",
            response_text
        )


        return jsonify({
            "response": response_text
        })


    # =====================================================
    # NORMAL AI CHAT
    # =====================================================

    save_chat_message(
        "user",
        message
    )


    answer = get_ai_response(
        message
    )


    save_chat_message(
        "assistant",
        answer
    )


    return jsonify({
        "response": answer
    })


# =========================================================
# CLEAR CHAT HISTORY
# =========================================================

@app.route("/clear-history", methods=["POST"])
def clear_history():

    try:

        with open(
            CHAT_HISTORY_FILE,
            "w"
        ) as file:

            json.dump(
                [],
                file,
                indent=4
            )


        return jsonify({
            "success": True,
            "message": "Chat history cleared."
        })


    except Exception as error:

        print(
            "CLEAR HISTORY ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Could not clear history."
        })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )