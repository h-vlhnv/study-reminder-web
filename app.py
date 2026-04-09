from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import sqlite3
from datetime import datetime, timedelta
import os
from werkzeug.routing import IntegerConverter
import hashlib


class NegativeIntConverter(IntegerConverter):
    regex = r"-?\d+"


app = Flask(__name__)
app.url_map.converters["negint"] = NegativeIntConverter
app.url_map.strict_slashes = False

app.secret_key = "study-reminder-secret-key"
DB_NAME = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        description TEXT,
        deadline TEXT,
        created_at TEXT,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.now().isoformat()),
        )
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def get_user_by_username(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, username, password FROM users WHERE username = ?", (username,)
    )
    user = c.fetchone()
    conn.close()
    return user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def get_tasks(user_id, include_completed=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if include_completed:
        c.execute(
            "SELECT id, description, deadline, completed FROM tasks WHERE user_id = ? ORDER BY deadline",
            (user_id,),
        )
    else:
        c.execute(
            "SELECT id, description, deadline, completed FROM tasks WHERE user_id = ? AND completed = 0 ORDER BY deadline",
            (user_id,),
        )
    tasks = c.fetchall()
    conn.close()
    return tasks


def add_task(user_id, description, deadline):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (user_id, description, deadline, created_at) VALUES (?, ?, ?, ?)",
        (user_id, description, deadline, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def complete_task(user_id, task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_task(user_id, task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("index", week_offset=0))
    return redirect(url_for("login"))


@app.route("/week/<negint:week_offset>")
@login_required
def index(week_offset=0):
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    week_days = []
    start_of_week = (
        today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    )
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        week_days.append(
            {
                "date": day,
                "date_str": day.strftime("%Y-%m-%d"),
                "day_name": day.strftime("%A"),
                "day_num": day.strftime("%d"),
            }
        )

    tasks = get_tasks(session["user_id"], include_completed=True)
    tasks_by_date = {}

    for task in tasks:
        deadline = datetime.strptime(task[2], "%Y-%m-%d")
        days_left = (deadline - today).days
        status = (
            "overdue"
            if days_left < 0 and not task[3]
            else (
                "urgent"
                if days_left <= 1 and not task[3]
                else ("soon" if days_left <= 3 and not task[3] else "normal")
            )
        )
        deadline_str = deadline.strftime("%Y-%m-%d")

        if deadline_str not in tasks_by_date:
            tasks_by_date[deadline_str] = {"active": [], "completed": []}

        task_data = {
            "id": task[0],
            "description": task[1],
            "deadline": deadline.strftime("%d.%m.%Y"),
            "completed": task[3],
            "days_left": days_left,
            "status": status,
        }

        if task[3]:
            tasks_by_date[deadline_str]["completed"].append(task_data)
        else:
            tasks_by_date[deadline_str]["active"].append(task_data)

    all_tasks = get_tasks(session["user_id"], include_completed=True)
    active_tasks = []
    completed_tasks = []

    for task in all_tasks:
        deadline = datetime.strptime(task[2], "%Y-%m-%d")
        days_left = (deadline - today).days
        status = (
            "overdue"
            if days_left < 0 and not task[3]
            else (
                "urgent"
                if days_left <= 1 and not task[3]
                else ("soon" if days_left <= 3 and not task[3] else "normal")
            )
        )
        task_data = {
            "id": task[0],
            "description": task[1],
            "deadline": deadline.strftime("%d.%m.%Y"),
            "completed": task[3],
            "days_left": days_left,
            "status": status,
        }

        if task[3]:
            completed_tasks.append(task_data)
        else:
            active_tasks.append(task_data)

    return render_template(
        "index.html",
        active_tasks=active_tasks,
        completed_tasks=completed_tasks,
        week_days=week_days,
        tasks_by_date=tasks_by_date,
        today_str=today.strftime("%Y-%m-%d"),
        week_offset=week_offset,
    )


@app.route("/add", methods=["POST"])
@login_required
def add():
    description = request.form.get("description")
    deadline = request.form.get("deadline")
    week_offset = request.args.get("week_offset", 0, type=int)

    if not description or not deadline:
        flash("Please fill in all fields!", "error")
        return redirect(url_for("index", week_offset=week_offset))

    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        if deadline_date < datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ):
            flash("Deadline cannot be in the past!", "error")
            return redirect(url_for("index", week_offset=week_offset))

        add_task(session["user_id"], description, deadline)
        flash("Task added!", "success")
    except ValueError:
        flash("Invalid date format!", "error")

    return redirect(url_for("index", week_offset=week_offset))


@app.route("/complete/<int:task_id>")
@login_required
def complete(task_id):
    week_offset = request.args.get("week_offset", 0, type=int)
    complete_task(session["user_id"], task_id)
    flash("Task completed!", "success")
    return redirect(url_for("index", week_offset=week_offset))


@app.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
    week_offset = request.args.get("week_offset", 0, type=int)
    delete_task(session["user_id"], task_id)
    flash("Task deleted!", "success")
    return redirect(url_for("index", week_offset=week_offset))

    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        if deadline_date < datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ):
            flash("Дата дедлайна не может быть в прошлом!", "error")
            return redirect(url_for("index", week_offset=week_offset))

        add_task(session["user_id"], description, deadline)
        flash("Задание добавлено!", "success")
    except ValueError:
        flash("Неверный формат даты!", "error")

    return redirect(url_for("index", week_offset=week_offset))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not username or not password:
            flash("Please fill in all fields!", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("register.html")

        if create_user(username, password):
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Username already exists!", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = get_user_by_username(username)
        if user and user[2] == hash_password(password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Logged in successfully!", "success")
            return redirect(url_for("index", week_offset=0))
        else:
            flash("Invalid username or password!", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out!", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
