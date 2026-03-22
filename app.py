from flask import Flask, request, redirect, render_template
import sqlite3
import string
import random

app = Flask(__name__)
DATABASE = "database.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("DROP TABLE IF EXISTS urls")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT UNIQUE,
                clicks INTEGER DEFAULT 0
            )
        """)

def save_url(original_url, short_code):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(
            "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
            (original_url.strip(), short_code.strip())
        )
        conn.commit()

def get_url(short_code):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT original_url FROM urls WHERE short_code = ?",
            (short_code,)
        )
        result = cursor.fetchone()
        if result:
            cursor.execute(
                "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?",
                (short_code,)
            )
            conn.commit()
            return result[0]
        return None

def code_exists(short_code):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute(
            "SELECT 1 FROM urls WHERE short_code = ?",
            (short_code,)
        )
        return cursor.fetchone() is not None

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_unique_code():
    while True:
        code = generate_short_code()
        if not code_exists(code):
            return code

def get_all_urls():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute(
            "SELECT original_url, short_code, clicks FROM urls"
        )
        return cursor.fetchall()

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = request.form["url"].strip()
        if not original_url.startswith(("http://", "https://")):
            original_url = "http://" + original_url
        short_code = generate_unique_code()
        save_url(original_url, short_code)
        short_url = request.host_url + short_code
        return render_template("result.html", short_url=short_url)
    return render_template("index.html")

@app.route("/<short_code>")
def redirect_url(short_code):
    original_url = get_url(short_code)
    if original_url:
        return redirect(original_url)
    else:
        return "URL not found", 404

@app.route("/stats")
def stats():
    urls = get_all_urls()
    return render_template("stats.html", urls=urls)

if __name__ == "__main__":
    init_db()
    app.run()