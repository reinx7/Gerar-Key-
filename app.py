from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, Email
import sqlite3
import os
import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DATABASE = "database.db"

# ---------------- Database ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password TEXT,
                    plan_expire DATETIME,
                    bot_token TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS proofs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    uploaded_at DATETIME
                 )''')
    conn.commit()
    conn.close()

init_db()

# ---------------- User ----------------
class User(UserMixin):
    def __init__(self, id_, username, email, plan_expire):
        self.id = id_
        self.username = username
        self.email = email
        self.plan_expire = plan_expire

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username, email, plan_expire FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

# ---------------- Forms ----------------
class RegisterForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(min=3)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=5)])
    submit = SubmitField("Registrar")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

# ---------------- Routes ----------------
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",
                      (form.username.data, form.email.data, form.password.data))
            conn.commit()
            flash("✅ Conta criada com sucesso!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("❌ Usuário ou email já cadastrado.", "danger")
        finally:
            conn.close()
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id, username, email, plan_expire, password FROM users WHERE email=?", (form.email.data,))
        row = c.fetchone()
        conn.close()
        if row and row[4] == form.password.data:
            user = User(row[0], row[1], row[2], row[3])
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("❌ Credenciais inválidas", "danger")
    return render_template("login.html", form=form)

@app.route("/dashboard", methods=["GET","POST"])
@login_required
def dashboard():
    if request.method == "POST":
        token = request.form.get("bot_token")
        plan = datetime.datetime.utcnow() + datetime.timedelta(days=1)  # 1 dia grátis
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE users SET bot_token=?, plan_expire=? WHERE id=?",
                  (token, plan, current_user.id))
        conn.commit()
        conn.close()
        flash("✅ Key grátis ativada e token salvo!", "success")
    return render_template("dashboard.html", user=current_user)

@app.route("/upload_proof", methods=["POST"])
@login_required
def upload_proof():
    file = request.files.get("file")
    if file:
        filename = f"{current_user.id}_{datetime.datetime.utcnow().timestamp()}_{file.filename}"
        path = os.path.join("static", "uploads")
        os.makedirs(path, exist_ok=True)
        file.save(os.path.join(path, filename))
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO proofs (user_id, filename, uploaded_at) VALUES (?,?,?)",
                  (current_user.id, filename, datetime.datetime.utcnow()))
        conn.commit()
        conn.close()
        flash("✅ Comprovante enviado!", "success")
    return redirect(url_for("dashboard"))

@app.route("/admin")
@login_required
def admin():
    if current_user.username != "admin":
        flash("❌ Acesso negado", "danger")
        return redirect(url_for("dashboard"))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username, email, plan_expire FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
