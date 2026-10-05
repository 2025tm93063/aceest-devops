import os
import random
import sqlite3
from datetime import date, datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aceest-secret-key-2026")

DB_NAME = os.environ.get("DB_PATH", "aceest_fitness.db")

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": "Mon: Back Squat 5x5 + Core\nTue: EMOM 20min Assault Bike\nWed: Bench Press + 21-15-9\nThu: Deadlift + Box Jumps\nFri: Zone 2 Cardio 30min",
        "diet": "Breakfast: Egg Whites + Oats\nLunch: Grilled Chicken + Brown Rice\nDinner: Fish Curry + Millet Roti\nTarget: ~2000 kcal",
        "calorie_factor": 22,
    },
    "Muscle Gain (MG)": {
        "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\nThu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
        "diet": "Breakfast: Eggs + Peanut Butter Oats\nLunch: Chicken Biryani\nDinner: Mutton Curry + Rice\nTarget: ~3200 kcal",
        "calorie_factor": 35,
    },
    "Beginner (BG)": {
        "workout": "Full Body Circuit:\n- Air Squats\n- Ring Rows\n- Push-ups\nFocus: Technique & Consistency",
        "diet": "Balanced Tamil Meals\nIdli / Dosa / Rice + Dal\nProtein Target: 120g/day",
        "calorie_factor": 26,
    },
}

PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"],
}


# ---------- DATABASE ----------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            target_adherence INTEGER,
            membership_status TEXT DEFAULT 'Active',
            membership_end TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week TEXT NOT NULL,
            adherence INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            weight REAL,
            waist REAL,
            bodyfat REAL
        )
    """)

    cur.execute("SELECT username FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin','admin123','Admin')")

    conn.commit()
    conn.close()


# ---------- AUTH HELPERS ----------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def calculate_calories(weight, program_name):
    program = PROGRAMS.get(program_name)
    if program and weight:
        return int(float(weight) * program["calorie_factor"])
    return 0


# ---------- ROUTES: AUTH ----------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        conn = get_db()
        user = conn.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()
        if user:
            session["username"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials. Please try again.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- ROUTES: DASHBOARD ----------

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    clients = conn.execute("SELECT name, program, membership_status FROM clients ORDER BY name").fetchall()
    conn.close()
    return render_template("dashboard.html", clients=clients, programs=list(PROGRAMS.keys()))


# ---------- ROUTES: CLIENTS ----------

@app.route("/client/add", methods=["GET", "POST"])
@login_required
def add_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age") or None
        height = request.form.get("height") or None
        weight = request.form.get("weight") or None
        program = request.form.get("program", "")
        target_weight = request.form.get("target_weight") or None
        target_adherence = request.form.get("target_adherence") or None
        membership_end = request.form.get("membership_end") or None
        calories = calculate_calories(weight, program)

        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO clients
                   (name, age, height, weight, program, calories,
                    target_weight, target_adherence, membership_status, membership_end)
                   VALUES (?,?,?,?,?,?,?,?,'Active',?)""",
                (name, age, height, weight, program, calories,
                 target_weight, target_adherence, membership_end)
            )
            conn.commit()
            flash(f"Client '{name}' added successfully.")
        except sqlite3.IntegrityError:
            flash(f"Client '{name}' already exists.")
        finally:
            conn.close()
        return redirect(url_for("dashboard"))

    return render_template("add_client.html", programs=list(PROGRAMS.keys()))


@app.route("/client/<name>")
@login_required
def client_profile(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        flash("Client not found.")
        conn.close()
        return redirect(url_for("dashboard"))

    progress = conn.execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    workouts = conn.execute(
        "SELECT date, workout_type, duration_min, notes FROM workouts WHERE client_name=? ORDER BY date DESC",
        (name,)
    ).fetchall()
    metrics = conn.execute(
        "SELECT date, weight, waist, bodyfat FROM metrics WHERE client_name=? ORDER BY date DESC",
        (name,)
    ).fetchall()
    conn.close()

    program_detail = PROGRAMS.get(client["program"], {})
    return render_template(
        "client_profile.html",
        client=client,
        program_detail=program_detail,
        progress=progress,
        workouts=workouts,
        metrics=metrics,
        today=date.today().isoformat(),
    )


@app.route("/client/<name>/generate_program")
@login_required
def generate_program(name):
    program_type = random.choice(list(PROGRAM_TEMPLATES.keys()))
    program_detail = random.choice(PROGRAM_TEMPLATES[program_type])
    conn = get_db()
    conn.execute("UPDATE clients SET program=? WHERE name=?", (program_detail, name))
    conn.commit()
    conn.close()
    flash(f"Program generated for {name}: {program_detail}")
    return redirect(url_for("client_profile", name=name))


# ---------- ROUTES: PROGRESS ----------

@app.route("/client/<name>/progress/add", methods=["POST"])
@login_required
def add_progress(name):
    adherence = request.form.get("adherence", 0)
    week = datetime.now().strftime("Week %U - %Y")
    conn = get_db()
    conn.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)",
        (name, week, adherence)
    )
    conn.commit()
    conn.close()
    flash("Progress logged.")
    return redirect(url_for("client_profile", name=name))


# ---------- ROUTES: WORKOUTS ----------

@app.route("/client/<name>/workout/add", methods=["POST"])
@login_required
def add_workout(name):
    conn = get_db()
    conn.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
        (
            name,
            request.form.get("date", date.today().isoformat()),
            request.form.get("workout_type", ""),
            request.form.get("duration_min", 60),
            request.form.get("notes", ""),
        )
    )
    conn.commit()
    conn.close()
    flash("Workout added.")
    return redirect(url_for("client_profile", name=name))


# ---------- ROUTES: METRICS ----------

@app.route("/client/<name>/metrics/add", methods=["POST"])
@login_required
def add_metrics(name):
    conn = get_db()
    conn.execute(
        "INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?,?,?,?,?)",
        (
            name,
            request.form.get("date", date.today().isoformat()),
            request.form.get("weight") or None,
            request.form.get("waist") or None,
            request.form.get("bodyfat") or None,
        )
    )
    conn.commit()
    conn.close()
    flash("Metrics saved.")
    return redirect(url_for("client_profile", name=name))


# ---------- ROUTES: ADMIN ----------

@app.route("/admin/add_user", methods=["GET", "POST"])
@login_required
def add_user():
    if session.get("role") != "Admin":
        flash("Admin access required.")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "Trainer")
        conn = get_db()
        try:
            conn.execute("INSERT INTO users VALUES (?,?,?)", (username, password, role))
            conn.commit()
            flash(f"User '{username}' created.")
        except sqlite3.IntegrityError:
            flash(f"User '{username}' already exists.")
        finally:
            conn.close()
        return redirect(url_for("dashboard"))
    return render_template("add_user.html")


# ---------- HEALTH CHECK (for CI) ----------

@app.route("/health")
def health():
    return {"status": "ok", "app": "ACEest Fitness"}, 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8081, debug=False)
