from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import json
import os
import re
import uuid
import ollama

# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "uniassist-secret-key-change-this"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]
)

# =========================================================
# ADMIN LOGIN
# =========================================================

# ONLY YOU KNOW THESE DETAILS
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

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
# DATA FILES
# =========================================================

DATA_FOLDER = "data"

REGISTRATION_FILE = os.path.join(
    DATA_FOLDER,
    "registrations.json"
)

CHAT_HISTORY_FILE = os.path.join(
    DATA_FOLDER,
    "chat_history.json"
)

os.makedirs(DATA_FOLDER, exist_ok=True)

# =========================================================
# AI INSTRUCTIONS
# =========================================================

AI_INSTRUCTIONS = """
You are UniAssist AI, a friendly educational assistant.

You can help students with:

- Artificial Intelligence
- Machine Learning
- Data Science
- Python
- Web Development
- Programming
- Courses
- Student registration
- Eligibility
- Internships
- College-related questions
- Projects
- General educational questions

Available UniAssist courses:

1. AI & Machine Learning
2. Data Science
3. Python Programming
4. Web Development

IMPORTANT:

Answer the user's actual question.

Do not respond only with keywords.

If the user asks about available courses, explain all four
UniAssist courses.

If the user asks about AI, explain Artificial Intelligence.

If the user asks about Machine Learning, explain Machine Learning.

If the user asks about Python, explain Python.

If the user asks about Data Science, explain Data Science.

If the user asks about Web Development, explain Web Development.

For general questions, answer naturally and helpfully.

Keep answers beginner-friendly.

Do not claim that registration was completed unless the
registration system actually completed it.

Do not invent personal information.

Use simple explanations and examples when useful.
"""

# =========================================================
# JSON HELPERS
# =========================================================

def load_json_file(filename, default):

    if not os.path.exists(filename):
        return default

    try:
        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except Exception as error:

        print(
            f"JSON LOAD ERROR ({filename}):",
            error
        )

        return default


def save_json_file(filename, data):

    try:

        os.makedirs(
            DATA_FOLDER,
            exist_ok=True
        )

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception as error:

        print(
            f"JSON SAVE ERROR ({filename}):",
            error
        )

        return False


# =========================================================
# REGISTRATION FUNCTIONS
# =========================================================

def load_registrations():

    data = load_json_file(
        REGISTRATION_FILE,
        []
    )

    if isinstance(data, list):
        return data

    return []


def save_registration():

    registrations = load_registrations()

    registration = {
        "id": len(registrations) + 1,
        "name": session.get("name", ""),
        "email": session.get("email", ""),
        "phone": session.get("phone", ""),
        "college": session.get("college", ""),
        "course": session.get("course", "")
    }

    registrations.append(registration)

    save_json_file(
        REGISTRATION_FILE,
        registrations
    )

    return registration


# =========================================================
# USER ID
# =========================================================

def get_user_id():

    user_id = session.get("user_id")

    if not user_id:

        user_id = str(
            uuid.uuid4()
        )

        session["user_id"] = user_id

    return user_id


# =========================================================
# CHAT HISTORY
# =========================================================

def load_chat_history():

    data = load_json_file(
        CHAT_HISTORY_FILE,
        []
    )

    if isinstance(data, list):
        return data

    return []


def save_chat_message(role, message):

    history = load_chat_history()

    user_id = get_user_id()

    history.append({
        "user_id": user_id,
        "role": role,
        "message": message
    })

    save_json_file(
        CHAT_HISTORY_FILE,
        history
    )


def get_my_chat_history():

    history = load_chat_history()

    user_id = get_user_id()

    return [
        item
        for item in history
        if item.get("user_id") == user_id
    ]


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin():

    return session.get(
        "is_admin",
        False
    ) is True


# =========================================================
# HOME
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
# ADMIN PAGE
# =========================================================

@app.route("/admin")
def admin_page():

    return render_template(
        "index.html"
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin-login",
    methods=["POST"]
)
@app.route(
    "/admin/login",
    methods=["POST"]
)
@app.route(
    "/api/admin/login",
    methods=["POST"]
)
def admin_login():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "success": False,
                "message": "No login data received."
            }), 400

        username = str(
            data.get(
                "username",
                ""
            )
        ).strip()

        password = str(
            data.get(
                "password",
                ""
            )
        )

        print(
            "ADMIN LOGIN ATTEMPT:",
            username
        )

        # ---------------------------------------------
        # CHECK ADMIN
        # ---------------------------------------------

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["is_admin"] = True
            session["admin_username"] = username

            # Make sure admin does not become a normal user
            # for the purpose of displaying student history.
            session.permanent = True

            print(
                "ADMIN LOGIN SUCCESS"
            )

            return jsonify({
                "success": True,
                "message": "Admin login successful.",
                "redirect": "/registrations"
            })

        print(
            "ADMIN LOGIN FAILED"
        )

        return jsonify({
            "success": False,
            "message": "Invalid admin username or password."
        }), 401

    except Exception as error:

        print(
            "ADMIN LOGIN ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Server error during admin login."
        }), 500


# =========================================================
# ADMIN STATUS
# =========================================================

@app.route(
    "/admin-status",
    methods=["GET"]
)
@app.route(
    "/api/admin/status",
    methods=["GET"]
)
def admin_status():

    return jsonify({
        "is_admin": is_admin(),
        "logged_in": is_admin(),
        "username": session.get(
            "admin_username"
        )
    })


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route(
    "/admin-logout",
    methods=["POST", "GET"]
)
def admin_logout():

    session.pop(
        "is_admin",
        None
    )

    session.pop(
        "admin_username",
        None
    )

    return jsonify({
        "success": True,
        "message": "Admin logged out."
    })


# =========================================================
# ADMIN REGISTRATIONS PAGE
# =========================================================

@app.route(
    "/registrations"
)
def registrations():

    # ---------------------------------------------
    # IMPORTANT:
    # NORMAL STUDENTS CANNOT SEE THIS
    # ---------------------------------------------

    if not is_admin():

        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Access Only</title>

            <style>

                body {
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background: #f5f0ff;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }

                .box {
                    background: white;
                    padding: 45px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow:
                        0 10px 35px rgba(0,0,0,0.15);
                    max-width: 500px;
                }

                h1 {
                    color: #6d28d9;
                }

                p {
                    color: #555;
                    font-size: 17px;
                    line-height: 1.5;
                }

                a {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 13px 25px;
                    background: #7c3aed;
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                }

            </style>

        </head>

        <body>

            <div class="box">

                <h1>🔐 Admin Access Only</h1>

                <p>
                    Only the project administrator can
                    view all student registrations.
                </p>

                <a href="/">
                    Go Back
                </a>

            </div>

        </body>
        </html>
        """

    registrations_data = load_registrations()

    try:

        return render_template(
            "registrations.html",
            registrations=registrations_data
        )

    except Exception:

        return jsonify({
            "success": True,
            "admin": True,
            "registrations": registrations_data,
            "total": len(registrations_data)
        })


# =========================================================
# ADMIN REGISTRATION API
# =========================================================

@app.route(
    "/admin/registrations",
    methods=["GET"]
)
@app.route(
    "/api/registrations",
    methods=["GET"]
)
def admin_registrations():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    registrations_data = load_registrations()

    return jsonify({
        "success": True,
        "registrations": registrations_data,
        "total": len(registrations_data)
    })


# =========================================================
# MY REGISTRATION
# =========================================================

@app.route(
    "/my-registration"
)
def my_registration():

    user_id = session.get(
        "user_id"
    )

    email = session.get(
        "email"
    )

    name = session.get(
        "name"
    )

    # ---------------------------------------------
    # If user has not registered
    # ---------------------------------------------

    if not email and not name:

        return jsonify({
            "registered": False,
            "message": "No registration found."
        })

    # ---------------------------------------------
    # Return ONLY this user's information
    # ---------------------------------------------

    return jsonify({
        "registered": True,
        "user_id": user_id,
        "name": session.get("name"),
        "email": session.get("email"),
        "phone": session.get("phone"),
        "college": session.get("college"),
        "course": session.get("course")
    })


# =========================================================
# USER CHAT HISTORY
# =========================================================

@app.route(
    "/history"
)
def history():

    # ---------------------------------------------
    # USER ONLY SEES THEIR OWN HISTORY
    # ---------------------------------------------

    my_history = get_my_chat_history()

    try:

        return render_template(
            "history.html",
            history=my_history
        )

    except Exception:

        return jsonify({
            "success": True,
            "history": my_history
        })


# =========================================================
# USER CHAT HISTORY API
# =========================================================

@app.route(
    "/api/history",
    methods=["GET"]
)
def api_history():

    my_history = get_my_chat_history()

    return jsonify({
        "success": True,
        "history": my_history
    })


# =========================================================
# ADMIN CHAT HISTORY
# =========================================================
# Admin can see all histories only if you specifically
# want this feature.
# =========================================================

@app.route(
    "/admin/chat-history",
    methods=["GET"]
)
def admin_chat_history():

    if not is_admin():

        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    history = load_chat_history()

    return jsonify({
        "success": True,
        "history": history
    })


# =========================================================
# CLEAR MY HISTORY
# =========================================================

@app.route(
    "/clear-history",
    methods=["POST"]
)
def clear_history():

    try:

        history = load_chat_history()

        user_id = get_user_id()

        new_history = [
            item
            for item in history
            if item.get("user_id") != user_id
        ]

        save_json_file(
            CHAT_HISTORY_FILE,
            new_history
        )

        return jsonify({
            "success": True,
            "message": "Your chat history was cleared."
        })

    except Exception as error:

        print(
            "CLEAR HISTORY ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Could not clear chat history."
        }), 500


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
        or
        "artificial intelligence" in text
        or
        text == "ai"
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

    return re.match(
        pattern,
        email
    ) is not None


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
# FAST AI RESPONSE
# =========================================================

def get_ai_response(message):

    text = message.lower().strip()

    # =====================================================
    # FAST COURSE RESPONSE
    # =====================================================

    if (
        "what courses" in text
        or
        "which courses" in text
        or
        "available courses" in text
        or
        "courses available" in text
        or
        "list of courses" in text
        or
        text in [
            "courses",
            "course"
        ]
    ):

        return (
            "📚 <b>Available UniAssist Courses:</b>"
            "<br><br>"

            "🤖 <b>AI & Machine Learning</b>"
            "<br>"
            "Learn Artificial Intelligence, "
            "Machine Learning and Deep Learning."
            "<br><br>"

            "📊 <b>Data Science</b>"
            "<br>"
            "Learn data analysis, statistics, "
            "visualization and machine learning."
            "<br><br>"

            "🐍 <b>Python Programming</b>"
            "<br>"
            "Learn Python programming from basics "
            "and build useful applications."
            "<br><br>"

            "🌐 <b>Web Development</b>"
            "<br>"
            "Learn HTML, CSS, JavaScript and "
            "web application development."
            "<br><br>"

            "😊 <b>Which course would you like "
            "to know more about?</b>"
        )

    # =====================================================
    # OLLAMA
    # =====================================================

    try:

        response = ollama.chat(

            model="qwen2.5:0.5b",

            messages=[

                {
                    "role": "system",
                    "content": AI_INSTRUCTIONS
                },

                {
                    "role": "user",
                    "content": message
                }

            ],

            options={

                "temperature": 0.2,

                "num_predict": 120,

                "num_ctx": 1024,

                "top_k": 20,

                "top_p": 0.8

            }

        )

        answer = response[
            "message"
        ][
            "content"
        ]

        return answer.strip()

    except Exception as error:

        print(
            "OLLAMA ERROR:",
            error
        )

        return (
            "⚠️ <b>Local AI is currently unavailable.</b>"
            "<br><br>"
            "Please make sure Ollama is running."
        )


# =========================================================
# CHAT API
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "response":
                    "🤖 I didn't receive your message."
            })

        message = str(
            data.get(
                "message",
                ""
            )
        ).strip()

        if not message:

            return jsonify({
                "response":
                    "😊 Please type something."
            })

        text = message.lower().strip()

        # ---------------------------------------------
        # MAKE USER ID
        # ---------------------------------------------

        get_user_id()

        # =================================================
        # CANCEL REGISTRATION
        # =================================================

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

        # =================================================
        # AVAILABLE COURSES
        # =================================================

        if (
            "what courses" in text
            or
            "which courses" in text
            or
            "available courses" in text
            or
            "courses available" in text
            or
            "list of courses" in text
            or
            text in [
                "courses",
                "course"
            ]
        ):

            response_text = (
                "📚 <b>Here are the available courses:</b>"
                "<br><br>"

                "🤖 <b>AI & Machine Learning</b>"
                "<br>"
                "Learn Artificial Intelligence, "
                "Machine Learning and Deep Learning."
                "<br><br>"

                "📊 <b>Data Science</b>"
                "<br>"
                "Learn data analysis, statistics, "
                "visualization and machine learning."
                "<br><br>"

                "🐍 <b>Python Programming</b>"
                "<br>"
                "Learn Python programming and "
                "build useful applications."
                "<br><br>"

                "🌐 <b>Web Development</b>"
                "<br>"
                "Learn HTML, CSS, JavaScript and "
                "web application development."
                "<br><br>"

                "😊 <b>Which course would you like "
                "to know more about?</b>"
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

        # =================================================
        # START REGISTRATION
        # =================================================

        if (
            text == "register"
            or
            text == "registration"
            or
            text == "registration guide"
            or
            "i want to register" in text
            or
            "start registration" in text
        ):

            # Clear previous registration data

            session.pop(
                "name",
                None
            )

            session.pop(
                "email",
                None
            )

            session.pop(
                "phone",
                None
            )

            session.pop(
                "college",
                None
            )

            session.pop(
                "course",
                None
            )

            session[
                "registration_step"
            ] = "name"

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

        # =================================================
        # REGISTRATION STEP
        # =================================================

        registration_step = session.get(
            "registration_step"
        )

        # =================================================
        # NAME
        # =================================================

        if registration_step == "name":

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

            session[
                "name"
            ] = message

            session[
                "registration_step"
            ] = "email"

            response_text = (
                f"Nice to meet you, "
                f"<b>{message}</b>! 😊"
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

        # =================================================
        # EMAIL
        # =================================================

        if registration_step == "email":

            if not valid_email(message):

                response_text = (
                    "📧 <b>Please enter a valid email.</b>"
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

            session[
                "email"
            ] = message

            session[
                "registration_step"
            ] = "phone"

            response_text = (
                "📧 <b>Email saved!</b>"
                "<br><br>"
                "Now enter your phone number."
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

        # =================================================
        # PHONE
        # =================================================

        if registration_step == "phone":

            if not valid_phone(message):

                response_text = (
                    "📱 <b>Please enter a valid "
                    "phone number.</b>"
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

            session[
                "phone"
            ] = phone

            session[
                "registration_step"
            ] = "college"

            response_text = (
                "📱 <b>Phone number saved!</b>"
                "<br><br>"
                "What is your college name?"
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

        # =================================================
        # COLLEGE
        # =================================================

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

            session[
                "college"
            ] = message

            session[
                "registration_step"
            ] = "course"

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

        # =================================================
        # COURSE
        # =================================================

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

            # ---------------------------------------------
            # SAVE COURSE
            # ---------------------------------------------

            session[
                "course"
            ] = selected_course

            # ---------------------------------------------
            # SAVE REGISTRATION
            # ---------------------------------------------

            registration = save_registration()

            name = session.get(
                "name"
            )

            email = session.get(
                "email"
            )

            phone = session.get(
                "phone"
            )

            college = session.get(
                "college"
            )

            session[
                "registration_step"
            ] = "completed"

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

                "✅ <b>Your registration has been "
                "saved successfully.</b>"
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
                "response": response_text,
                "registration": registration
            })

        # =================================================
        # NORMAL AI CHAT
        # =================================================

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

    except Exception as error:

        print(
            "CHAT ERROR:",
            error
        )

        return jsonify({
            "response":
                "⚠️ Something went wrong on the server."
        }), 500


# =========================================================
# RESET SESSION
# =========================================================

@app.route(
    "/reset"
)
def reset():

    session.clear()

    return redirect("/")


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
@app.route(
    "/api/health"
)
def health():

    return jsonify({

        "status": "online",

        "application": "UniAssist AI",

        "ollama": "enabled",

        "courses": len(COURSES),

        "admin_system": "enabled",

        "user_chat_history": "enabled"

    })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )

    print(
        "          UniAssist AI Server"
    )

    print(
        "=========================================="
    )

    print(
        "Server:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()

    print(
        "Admin username: admin"
    )

    print(
        "Admin password: admin123"
    )

    print()

    print(
        "Normal user:"
    )

    print(
        "http://127.0.0.1:5000/"
    )

    print()

    print(
        "Admin registrations:"
    )

    print(
        "http://127.0.0.1:5000/registrations"
    )

    print(
        "=========================================="
    )

    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )