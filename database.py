import sqlite3
import os
from werkzeug.security import generate_password_hash


# =========================================================
# DATABASE LOCATION
# =========================================================

DATABASE = "data/uniassist.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    # Create data folder if it does not exist
    os.makedirs("data", exist_ok=True)

    connection = sqlite3.connect(DATABASE)

    # Allows us to access columns by name
    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    connection = get_connection()
    cursor = connection.cursor()


    # =====================================================
    # USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL DEFAULT 'student',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # =====================================================
    # COURSES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT UNIQUE NOT NULL,

            description TEXT
        )
    """)


    # =====================================================
    # REGISTRATIONS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            course_id INTEGER NOT NULL,

            phone TEXT,

            college TEXT,

            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id),

            FOREIGN KEY(course_id)
            REFERENCES courses(id)
        )
    """)


    # =====================================================
    # CHAT HISTORY TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            role TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
        )
    """)


    # =====================================================
    # INSERT COURSES
    # =====================================================

    courses = [

        (
            "AI & Machine Learning",
            "Learn Artificial Intelligence and Machine Learning."
        ),

        (
            "Data Science",
            "Learn statistics, data analysis and machine learning."
        ),

        (
            "Python Programming",
            "Learn Python programming from beginner to advanced."
        ),

        (
            "Web Development",
            "Learn HTML, CSS, JavaScript and web development."
        )

    ]


    for name, description in courses:

        cursor.execute("""
            INSERT OR IGNORE INTO courses
            (
                name,
                description
            )

            VALUES (?, ?)
        """, (
            name,
            description
        ))


    # =====================================================
    # CREATE DEFAULT ADMIN
    # =====================================================

    admin_email = "admin@uniassist.com"


    cursor.execute("""
        SELECT id

        FROM users

        WHERE email = ?
    """, (
        admin_email,
    ))


    admin = cursor.fetchone()


    if not admin:

        admin_password = generate_password_hash(
            "Admin@123"
        )


        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )

            VALUES (?, ?, ?, ?)
        """, (
            "UniAssist Admin",
            admin_email,
            admin_password,
            "admin"
        ))


    # =====================================================
    # SAVE DATABASE
    # =====================================================

    connection.commit()

    connection.close()


# =========================================================
# USER FUNCTIONS
# =========================================================

def create_user(
    name,
    email,
    password
):

    connection = get_connection()
    cursor = connection.cursor()


    hashed_password = generate_password_hash(
        password
    )


    try:

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )

            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            "student"
        ))


        user_id = cursor.lastrowid


        connection.commit()


        return user_id


    except sqlite3.IntegrityError:

        return None


    finally:

        connection.close()


# =========================================================
# GET USER BY EMAIL
# =========================================================

def get_user_by_email(email):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM users

        WHERE email = ?
    """, (
        email,
    ))


    user = cursor.fetchone()


    connection.close()


    if user:

        return dict(user)


    return None


# =========================================================
# GET USER BY ID
# =========================================================

def get_user_by_id(user_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM users

        WHERE id = ?
    """, (
        user_id,
    ))


    user = cursor.fetchone()


    connection.close()


    if user:

        return dict(user)


    return None


# =========================================================
# GET ALL STUDENTS
# =========================================================

def get_all_students():

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            name,
            email,
            created_at

        FROM users

        WHERE role = 'student'

        ORDER BY id DESC
    """)


    students = [

        dict(row)

        for row in cursor.fetchall()

    ]


    connection.close()


    return students


# =========================================================
# COURSE FUNCTIONS
# =========================================================

def get_courses():

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM courses

        ORDER BY id
    """)


    courses = [

        dict(row)

        for row in cursor.fetchall()

    ]


    connection.close()


    return courses


# =========================================================
# GET ONE COURSE
# =========================================================

def get_course(course_name):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM courses

        WHERE name = ?
    """, (
        course_name,
    ))


    course = cursor.fetchone()


    connection.close()


    if course:

        return dict(course)


    return None


# =========================================================
# REGISTRATION
# =========================================================

def create_registration(
    user_id,
    course_id,
    phone,
    college
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO registrations
        (
            user_id,
            course_id,
            phone,
            college
        )

        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        course_id,
        phone,
        college
    ))


    registration_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return registration_id


# =========================================================
# GET MY REGISTRATION
# =========================================================

def get_my_registration(user_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            registrations.id,

            users.name,

            users.email,

            registrations.phone,

            registrations.college,

            courses.name AS course,

            registrations.registered_at


        FROM registrations


        JOIN users

        ON registrations.user_id = users.id


        JOIN courses

        ON registrations.course_id = courses.id


        WHERE registrations.user_id = ?


        ORDER BY registrations.id DESC

    """, (
        user_id,
    ))


    registrations = [

        dict(row)

        for row in cursor.fetchall()

    ]


    connection.close()


    return registrations


# =========================================================
# GET ALL REGISTRATIONS
# ADMIN ONLY
# =========================================================

def get_all_registrations():

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            registrations.id,

            users.name,

            users.email,

            registrations.phone,

            registrations.college,

            courses.name AS course,

            registrations.registered_at


        FROM registrations


        JOIN users

        ON registrations.user_id = users.id


        JOIN courses

        ON registrations.course_id = courses.id


        ORDER BY registrations.id DESC

    """)


    registrations = [

        dict(row)

        for row in cursor.fetchall()

    ]


    connection.close()


    return registrations


# =========================================================
# CHAT HISTORY
# =========================================================

def save_chat(
    user_id,
    role,
    message
):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO chat_history
        (
            user_id,
            role,
            message
        )

        VALUES (?, ?, ?)
    """, (
        user_id,
        role,
        message
    ))


    connection.commit()

    connection.close()


# =========================================================
# GET MY CHAT HISTORY
# =========================================================

def get_my_chat_history(user_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        SELECT

            id,

            role,

            message,

            created_at


        FROM chat_history


        WHERE user_id = ?


        ORDER BY id ASC

    """, (
        user_id,
    ))


    history = [

        dict(row)

        for row in cursor.fetchall()

    ]


    connection.close()


    return history


# =========================================================
# CLEAR MY CHAT HISTORY
# =========================================================

def clear_my_chat_history(user_id):

    connection = get_connection()
    cursor = connection.cursor()


    cursor.execute("""
        DELETE FROM chat_history

        WHERE user_id = ?
    """, (
        user_id,
    ))


    connection.commit()

    connection.close()


# =========================================================
# STATISTICS
# =========================================================

def get_statistics():

    connection = get_connection()
    cursor = connection.cursor()


    # Students
    cursor.execute("""
        SELECT COUNT(*) AS count

        FROM users

        WHERE role = 'student'
    """)


    students = cursor.fetchone()["count"]


    # Courses
    cursor.execute("""
        SELECT COUNT(*) AS count

        FROM courses
    """)


    courses = cursor.fetchone()["count"]


    # Registrations
    cursor.execute("""
        SELECT COUNT(*) AS count

        FROM registrations
    """)


    registrations = cursor.fetchone()["count"]


    # Chat messages
    cursor.execute("""
        SELECT COUNT(*) AS count

        FROM chat_history
    """)


    messages = cursor.fetchone()["count"]


    connection.close()


    return {

        "students": students,

        "courses": courses,

        "registrations": registrations,

        "messages": messages

    }


# =========================================================
# TEST DATABASE
# =========================================================

if __name__ == "__main__":

    init_database()

    print()
    print("=" * 50)
    print("DATABASE CREATED SUCCESSFULLY!")
    print("=" * 50)
    print()
    print("Database location:")
    print(DATABASE)
    print()
    print("Default Admin:")
    print("Email: admin@uniassist.com")
    print("Password: Admin@123")
    print()
    print("Available courses:")

    for course in get_courses():

        print(
            "-",
            course["name"]
        )

    print()
    print("=" * 50)