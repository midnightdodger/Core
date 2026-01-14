from flask import Flask, render_template, redirect, session, request, send_from_directory
from werkzeug.utils import secure_filename
from lambda_utils import get_key, get_json
import secrets, bcrypt, sqlite3, os
from datetime import datetime
#waitress


app = Flask(__name__)
app.secret_key = get_key("data/key.data")
USER_ROOT = os.path.join(app.root_path, "users")
DEFAULT_PFP_URL = "/user/default.png"
os.makedirs(USER_ROOT, exist_ok=True)
ALLOWED_PFP_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".png", ".webp"}

def ensure_user_folder(user_id):
    os.makedirs(os.path.join(USER_ROOT, str(user_id)), exist_ok=True)

def get_user_pfp_url(user_id):
    user_dir = os.path.join(USER_ROOT, str(user_id))
    if os.path.isdir(user_dir):
        preferred = ["pfp.gif", "pfp.jpg", "pfp.jpeg", "pfp.png", "pfp.webp"]
        for filename in preferred:
            candidate = os.path.join(user_dir, filename)
            if os.path.exists(candidate):
                return f"/users/{user_id}/{filename}"
        for filename in sorted(os.listdir(user_dir)):
            if filename.startswith("pfp."):
                return f"/users/{user_id}/{filename}"
    return DEFAULT_PFP_URL

def get_user_pfp_filename(user_id):
    user_dir = os.path.join(USER_ROOT, str(user_id))
    if os.path.isdir(user_dir):
        preferred = ["pfp.gif", "pfp.jpg", "pfp.jpeg", "pfp.png", "pfp.webp"]
        for filename in preferred:
            candidate = os.path.join(user_dir, filename)
            if os.path.exists(candidate):
                return filename
        for filename in sorted(os.listdir(user_dir)):
            if filename.startswith("pfp."):
                return filename
    return os.path.basename(DEFAULT_PFP_URL)

def get_user_email(user_id):
    with sqlite3.connect("data/users/users.db") as con:
        cur = con.cursor()
        cur.execute("SELECT email FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    if row is None:
        return ""
    return row[0] or ""

def is_allowed_pfp(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_PFP_EXTENSIONS

def get_architecture_from_ua(user_agent_string):
    ua = (user_agent_string or "").lower()
    if "aarch64" in ua or "arm64" in ua:
        return "arm64"
    if "armv7" in ua or "armv8" in ua or "arm" in ua:
        return "arm"
    if "x86_64" in ua or "win64" in ua or "x64" in ua:
        return "x64"
    if "i686" in ua or "x86" in ua:
        return "x86"
    return "Unknown"
@app.route("/")
def index():
    try:
        user = {
            'username': session["username"],
            'user_id': session["user_id"],
            'pfp': get_user_pfp_url(session["user_id"]),
            'tags': request.cookies.get('tags')
        }
    except:
        user = {
            'username': "Sign in for more features",
            'user_id': " its Free!",
            'pfp': DEFAULT_PFP_URL,
            'tags': request.cookies.get('tags')
        }
    apps = get_json("data/JSON/apps.json")
    settings = get_json("data/JSON/settings.json")
    blog = get_json("data/JSON/blog.json")
    return render_template("Core.html", apps=apps, settings=settings, user=user, blog=blog)

@app.route("/<service>/account")
def account(service):
    return render_template("account.html", service=service)
    
@app.route("/check_account", methods=["GET", "POST"])
def check():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect("data/users/users.db") as con:
            cur = con.cursor()
            cur.execute(
                "SELECT user_id, username, password FROM users WHERE username = ?",
                (username,)
            )
            user = cur.fetchone()

        if user is None:
            if not username or not password:
                return "error - missing username or password"
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            with sqlite3.connect("data/users/users.db") as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO users (email, username, password, folder, glyph) VALUES (?, ?, ?, ?, ?)",
                    ("", username, password_hash, username, "")
                )
                user_id = cur.lastrowid
            session["username"] = username
            session["user_id"] = user_id
            ensure_user_folder(user_id)
            return redirect("/")

        stored_hash = user[2].encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            session["username"] = user[1]
            session["user_id"] = user[0]
            ensure_user_folder(user[0])
            return redirect("/")
        else:
            return "error - wrong password"

    return redirect("/")

@app.route("/users/<path:filename>")
def users(filename):
    return send_from_directory(USER_ROOT, filename)

@app.route("/user/<path:filename>")
def user_defaults(filename):
    return send_from_directory(USER_ROOT, filename)

@app.route("/settings/identity", methods=["GET", "POST"])
def identity():
    if request.method == "POST":
        if "user_id" not in session:
            return redirect("/")
        user_id = session["user_id"]
        file = request.files.get("pfp")
        email = request.form.get("email", "").strip()
        remove_email = request.form.get("remove_email")

        if file and file.filename:
            safe_name = secure_filename(file.filename)
            if not safe_name or not is_allowed_pfp(safe_name):
                return "error - invalid file type"
            ensure_user_folder(user_id)
            user_dir = os.path.join(USER_ROOT, str(user_id))
            for filename in os.listdir(user_dir):
                if filename.startswith("pfp."):
                    os.remove(os.path.join(user_dir, filename))
            _, ext = os.path.splitext(safe_name)
            file.save(os.path.join(user_dir, f"pfp{ext.lower()}"))
        if remove_email is not None:
            with sqlite3.connect("data/users/users.db") as con:
                cur = con.cursor()
                cur.execute("UPDATE users SET email = ? WHERE user_id = ?", ("", user_id))
        elif email:
            with sqlite3.connect("data/users/users.db") as con:
                cur = con.cursor()
                cur.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, user_id))
        return redirect("/settings/identity")
    user_id = session.get("user_id")
    email = get_user_email(user_id) if user_id else ""
    pfp_filename = get_user_pfp_filename(user_id) if user_id else os.path.basename(DEFAULT_PFP_URL)
    return render_template("settings/identity.html", username=session.get("username"), email=email, pfp_filename=pfp_filename)

@app.route("/settings/themes")
def themes():
    return render_template("placeholders/unavalible.html")
    
@app.route("/settings/accessibility")
def accessiblity():
    return render_template("placeholders/unavalible.html")
    
@app.route("/settings/services")
def services():
    return render_template("placeholders/unavalible.html")
    
@app.route("/settings/security")
def security():
    return render_template("placeholders/unavalible.html")
    
@app.route("/settings/wellbeing")
def wellbeing():
    return render_template("placeholders/unavalible.html")
    
@app.route("/settings/privacy")
def privacy():
    return render_template("settings/privacy.html")
    

@app.route("/settings/session")
def settings_session():
    if "user_id" not in session:
        return render_template("settings/session.html", sessions=[], signed_in=False)
    ua = request.user_agent
    platform = ua.platform or "Unknown OS"
    device = "Mobile" if ua.platform in {"android", "iphone", "ipad"} else "Desktop"
    browser = ua.browser or "Unknown Browser"
    browser_version = ua.version or ""
    arch = get_architecture_from_ua(ua.string)
    sessions = [
        {
            "ip": request.remote_addr or "Unknown",
            "time": datetime.now().strftime("%m/%d/%Y - %H:%M"),
            "device": device,
            "os": platform,
            "browser": f"{browser} {browser_version}".strip(),
            "arch": arch,
            "current": True,
        }
    ]
    return render_template("settings/session.html", sessions=sessions, signed_in=True)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")
    
@app.route("/settings/advanced")
def advanced():
    return render_template("settings/advanced.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("Error.html", reason="Page not found!", code="404", support="/")
if __name__ == "__main__":
    with sqlite3.connect('data/users/users.db') as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, email TEXT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, folder TEXT NOT NULL, glyph TEXT)")
    app.run(debug = True)
