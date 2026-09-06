from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
from groq import Groq

import os
import json
import re
import uuid


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "uniassist-secret-key-change-this"
)

CORS(
    app,
    supports_credentials=True
)

# =========================================================
# GROQ CONFIGURATION
# =========================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )
else:
    groq_client = None

GROQ_MODEL = "llama-3.3-70b-versatile"


# =========================================================
# ADMIN LOGIN
# =========================================================

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
# DATA FOLDER
# =========================================================

DATA_FOLDER = "data"

os.makedirs(
    DATA_FOLDER,
    exist_ok=True
)


REGISTRATION_FILE = os.path.join(
    DATA_FOLDER,
    "registrations.json"
)

CHAT_HISTORY_FILE = os.path.join(
    DATA_FOLDER,
    "chat_history.json"
)


# =========================================================
# AI INSTRUCTIONS
# =========================================================

AI_INSTRUCTIONS = """
You are UniAssist AI, a helpful educational assistant.

You help students with:

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

If the user asks about available courses, explain these four courses.

If the user asks about AI, explain AI simply.

If the user asks about Machine Learning, explain Machine Learning simply.

If the user asks about Python, explain Python simply.

If the user asks about Data Science, explain Data Science simply.

If the user asks about Web Development, explain Web Development simply.

Answer the user's actual question.

Keep answers beginner-friendly.

Do not claim that a registration was completed unless the registration
system actually completed it.

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
            "JSON LOAD ERROR:",
            filename,
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
            "JSON SAVE ERROR:",
            filename,
            error
        )

        return False


# =========================================================
# REGISTRATIONS
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

        "name": session.get(
            "name",
            ""
        ),

        "email": session.get(
            "email",
            ""
        ),

        "phone": session.get(
            "phone",
            ""
        ),

        "college": session.get(
            "college",
            ""
        ),

        "course": session.get(
            "course",
            ""
        )

    }

    registrations.append(
        registration
    )

    save_json_file(
        REGISTRATION_FILE,
        registrations
    )

    return registration


# =========================================================
# CHAT HISTORY
# =========================================================

def get_user_id():

    if "user_id" not in session:

        session["user_id"] = str(
            uuid.uuid4()
        )

    return session["user_id"]


def load_chat_history():

    data = load_json_file(
        CHAT_HISTORY_FILE,
        []
    )

    if isinstance(data, list):
        return data

    return []


def save_chat_message(
    role,
    message
):

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

        if item.get(
            "user_id"
        ) == user_id

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
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    registrations = load_registrations()

    return render_template(
        "index.html",
        total_students=len(
            registrations
        ),
        total_courses=len(
            COURSES
        ),
        total_registrations=len(
            registrations
        )
    )


# =========================================================
# ADMIN PAGE
# =========================================================

@app.route("/admin")
def admin_page():

    if not is_admin():

        return redirect("/")

    registrations = load_registrations()

    try:

        return render_template(
            "admin.html",
            registrations=registrations
        )

    except Exception:

        return jsonify({

            "success": True,

            "admin": True,

            "registrations":
                registrations,

            "total":
                len(registrations)

        })


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

                "message":
                    "No login data received."

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

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["is_admin"] = True

            session[
                "admin_username"
            ] = username

            session.permanent = True

            return jsonify({

                "success": True,

                "message":
                    "Admin login successful.",

                "redirect":
                    "/admin"

            })

        return jsonify({

            "success": False,

            "message":
                "Invalid admin username or password."

        }), 401

    except Exception as error:

        print(
            "ADMIN LOGIN ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Server error during admin login."

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

        "is_admin":
            is_admin(),

        "logged_in":
            is_admin(),

        "username":
            session.get(
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

        "message":
            "Admin logged out."

    })


# =========================================================
# ADMIN REGISTRATIONS PAGE
# =========================================================

@app.route(
    "/registrations"
)
def registrations():

    if not is_admin():

        return """

        <!DOCTYPE html>

        <html>

        <head>

        <title>Admin Access Required</title>

        <style>

        body {
            font-family: Arial;
            background: #f5f2ff;
            text-align: center;
            padding-top: 100px;
        }

        .box {
            background: white;
            padding: 40px;
            border-radius: 20px;
            display: inline-block;
            box-shadow: 0 10px 30px rgba(0,0,0,.15);
        }

        h1 {
            color: #6d28d9;
        }

        a {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 25px;
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
        Only the project administrator can view
        all student registrations.
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

            "registrations":
                registrations_data,

            "total":
                len(registrations_data)

        })


# =========================================================
# ADMIN REGISTRATION API
# =========================================================

@app.route(
    "/api/registrations",
    methods=["GET"]
)
@app.route(
    "/admin/registrations",
    methods=["GET"]
)
def api_registrations():

    if not is_admin():

        return jsonify({

            "success": False,

            "message":
                "Admin access required."

        }), 403

    registrations_data = load_registrations()

    return jsonify({

        "success": True,

        "admin": True,

        "registrations":
            registrations_data,

        "total":
            len(registrations_data)

    })


# =========================================================
# CONFIGURATION CHECK
# =========================================================

@app.route(
    "/api/config",
    methods=["GET"]
)
def api_config():

    return jsonify({

        "has_key":
            bool(GROQ_API_KEY),

        "ai_provider":
            "Groq",

        "model":
            GROQ_MODEL

    })


# =========================================================
# MY REGISTRATION
# =========================================================

@app.route(
    "/my-registration"
)
def my_registration():

    email = session.get(
        "email"
    )

    name = session.get(
        "name"
    )

    if not email and not name:

        return jsonify({

            "registered":
                False,

            "message":
                "No registration found."

        })

    return jsonify({

        "registered":
            True,

        "name":
            session.get(
                "name"
            ),

        "email":
            session.get(
                "email"
            ),

        "phone":
            session.get(
                "phone"
            ),

        "college":
            session.get(
                "college"
            ),

        "course":
            session.get(
                "course"
            )

    })


# =========================================================
# CHAT HISTORY PAGE
# =========================================================

@app.route(
    "/history"
)
def history():

    my_history = get_my_chat_history()

    try:

        return render_template(
            "history.html",
            history=my_history
        )

    except Exception:

        return jsonify({

            "success": True,

            "history":
                my_history

        })


# =========================================================
# CHAT HISTORY API
# =========================================================

@app.route(
    "/api/history",
    methods=["GET"]
)
def api_history():

    return jsonify({

        "success": True,

        "history":
            get_my_chat_history()

    })


# =========================================================
# CLEAR CHAT HISTORY
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

            if item.get(
                "user_id"
            ) != user_id

        ]

        save_json_file(
            CHAT_HISTORY_FILE,
            new_history
        )

        return jsonify({

            "success": True,

            "message":
                "Your chat history was cleared."

        })

    except Exception as error:

        print(
            "CLEAR HISTORY ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Could not clear chat history."

        }), 500


# =========================================================
# COURSE DETECTION
# =========================================================

def detect_course(message):

    text = message.lower().strip()

    if (
        "data science"
        in text
    ):

        return "Data Science"

    if (
        "python"
        in text
    ):

        return "Python Programming"

    if (
        "machine learning"
        in text
        or
        "artificial intelligence"
        in text
        or
        text == "ai"
        or
        text == "artificial intelligence"
    ):

        return "AI & Machine Learning"

    if (
        "web development"
        in text
        or
        "web development course"
        in text
    ):

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

    return (
        re.match(
            pattern,
            email
        )
        is not None
    )


# =========================================================
# PHONE VALIDATION
# =========================================================

def valid_phone(phone):

    digits = re.sub(
        r"\D",
        "",
        phone
    )

    return len(
        digits
    ) >= 10


# =========================================================
# GROQ AI RESPONSE
# =========================================================

def get_ai_response(message):

    if not GROQ_API_KEY or not groq_client:

        return (

            "⚠️ <b>AI service is not configured.</b>"
            "<br><br>"
            "Please add the <b>GROQ_API_KEY</b> "
            "environment variable on Render."

        )

    try:

        response = groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[

                {
                    "role":
                        "system",

                    "content":
                        AI_INSTRUCTIONS
                },

                {
                    "role":
                        "user",

                    "content":
                        message
                }

            ],

            temperature=0.2,

            max_tokens=500

        )

        answer = response.choices[
            0
        ].message.content

        if not answer:

            return (
                "Sorry, I could not generate a response."
            )

        return answer.strip()

    except Exception as error:

        print(
            "GROQ ERROR:",
            error
        )

        return (

            "⚠️ <b>AI service temporarily unavailable.</b>"
            "<br><br>"
            "Please try again in a moment."

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
                    "🤖 I didn't receive your message.",

                "reply":
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
                    "😊 Please type something.",

                "reply":
                    "😊 Please type something."

            })

        get_user_id()

        text = message.lower().strip()


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

            )

            save_chat_message(
                "assistant",
                response_text
            )

            return jsonify({

                "response":
                    response_text,

                "reply":
                    response_text

            })


        # =================================================
        # AVAILABLE COURSES
        # =================================================

        if (

            "what courses"
            in text

            or

            "which courses"
            in text

            or

            "available courses"
            in text

            or

            "courses available"
            in text

            or

            "list of courses"
            in text

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
                "Learn Python programming and build applications."
                "<br><br>"

                "🌐 <b>Web Development</b>"
                "<br>"
                "Learn HTML, CSS, JavaScript and web applications."
                "<br><br>"

                "😊 <b>Which course would you like to know more about?</b>"

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

                "response":
                    response_text,

                "reply":
                    response_text

            })


        # =================================================
        # START REGISTRATION
        # =================================================

        if (

            text == "register"

            or

            text == "registration"

            or

            "i want to register"
            in text

            or

            "start registration"
            in text

            or

            "register me"
            in text

        ):

            for key in [

                "name",
                "email",
                "phone",
                "college",
                "course"

            ]:

                session.pop(
                    key,
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

                "response":
                    response_text,

                "reply":
                    response_text

            })


        registration_step = session.get(
            "registration_step"
        )


        # =================================================
        # NAME
        # =================================================

        if registration_step == "name":

            if len(message) < 2:

                return jsonify({

                    "response":
                        "😊 Please enter your full name.",

                    "reply":
                        "😊 Please enter your full name."

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

                "response":
                    response_text,

                "reply":
                    response_text

            })


        # =================================================
        # EMAIL
        # =================================================

        if registration_step == "email":

            if not valid_email(message):

                response_text = (

                    "📧 <b>Please enter a valid email.</b>"
                    "<br><br>"
                    "Example: student@gmail.com"

                )

                return jsonify({

                    "response":
                        response_text,

                    "reply":
                        response_text

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

                "response":
                    response_text,

                "reply":
                    response_text

            })


        # =================================================
        # PHONE
        # =================================================

        if registration_step == "phone":

            if not valid_phone(message):

                response_text = (
                    "📱 Please enter a valid phone number."
                )

                return jsonify({

                    "response":
                        response_text,

                    "reply":
                        response_text

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

                "response":
                    response_text,

                "reply":
                    response_text

            })


        # =================================================
        # COLLEGE
        # =================================================

        if registration_step == "college":

            if len(message) < 2:

                response_text = (
                    "🎓 Please enter your college name."
                )

                return jsonify({

                    "response":
                        response_text,

                    "reply":
                        response_text

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

                "response":
                    response_text,

                "reply":
                    response_text

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

                    "🎓 Please choose one of these courses:"
                    "<br><br>"
                    "🤖 AI & Machine Learning"
                    "<br>"
                    "📊 Data Science"
                    "<br>"
                    "🐍 Python Programming"
                    "<br>"
                    "🌐 Web Development"

                )

                return jsonify({

                    "response":
                        response_text,

                    "reply":
                        response_text

                })

            session[
                "course"
            ] = selected_course

            registration = save_registration()

            name = session.get(
                "name",
                ""
            )

            email = session.get(
                "email",
                ""
            )

            phone = session.get(
                "phone",
                ""
            )

            college = session.get(
                "college",
                ""
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

                "✅ <b>Your registration has been saved successfully.</b>"

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

                "response":
                    response_text,

                "reply":
                    response_text,

                "registration":
                    registration

            })


        # =================================================
        # NORMAL GROQ AI CHAT
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

            "response":
                answer,

            "reply":
                answer

        })


    except Exception as error:

        print(
            "CHAT ERROR:",
            error
        )

        error_message = (
            "⚠️ Something went wrong on the server."
        )

        return jsonify({

            "response":
                error_message,

            "reply":
                error_message

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

        "status":
            "online",

        "application":
            "UniAssist AI",

        "ai_provider":
            "Groq",

        "groq_configured":
            bool(GROQ_API_KEY),

        "model":
            GROQ_MODEL,

        "courses":
            len(COURSES)

    })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

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
        f"Server Port: {port}"
    )
    print(
        "AI Provider: Groq"
    )
    print(
        f"Groq API Configured: {bool(GROQ_API_KEY)}"
    )
    print(
        f"Model: {GROQ_MODEL}"
    )
    print(
        "Admin username: admin"
    )
    print(
        "Admin password: admin123"
    )
    print(
        "Admin page: /admin"
    )
    print(
        "Registrations: /registrations"
    )
    print(
        "=========================================="
    )
    print()

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
