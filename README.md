from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import random
import string
import smtplib
import os

app = Flask(__name__)
app.secret_key = "segredo_super"

# ===== CONFIG =====
PIX_KEY = "SUA_CHAVE_PIX"
EMAIL = "SEUEMAIL@gmail.com"
EMAIL_PASS = "SENHA_APP"

ADMIN_USER = "InnerPsyche"
ADMIN_PASS = "lhayza"

ADMIN_URL = "/painel_innerpsyche_admin_9821"

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

# ===== DATABASE =====

def db():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def create_tables():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    email TEXT,
    password TEXT,
    key TEXT,
    approved INTEGER DEFAULT 0,
    bot_token TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plano TEXT,
    proof TEXT,
    status TEXT DEFAULT 'pendente'
    )
    """)

    con.commit()
    con.close()

create_tables()

# ===== HELPERS =====

def make_key():
    return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(12))

def send_email(destino,key):

    msg=f"""Subject: SUA KEY DO BOT

Compra aprovada!

Sua KEY:
{key}
"""

    server=smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login(EMAIL,EMAIL_PASS)
    server.sendmail(EMAIL,destino,msg)
    server.quit()

# ===== DESIGN =====

STYLE="""
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial;}
body{
background:linear-gradient(135deg,#0f0f12,#161621,#0d1117);
color:white;
display:flex;
justify-content:center;
padding:20px;
}
.card{
background:rgba(20,20,30,.9);
padding:30px;
border-radius:20px;
width:95%;
max-width:450px;
margin-top:20px;
box-shadow:0 0 30px #000;
}
input,select{
width:100%;
padding:12px;
margin:8px 0;
border:none;
border-radius:10px;
background:#111;
color:white;
}
button{
width:100%;
padding:12px;
margin-top:10px;
border:none;
border-radius:10px;
background:linear-gradient(90deg,#5865f2,#7289da);
color:white;
font-weight:bold;
cursor:pointer;
}
button:hover{opacity:.9;}
img{max-width:100%;}
</style>
"""

# ===== HOME =====

@app.route("/")
def home():
    return render_template_string(STYLE+"""
    <div class='card'>
    <h1>🔥 Loja Oficial</h1>
    <p>PIX:</p>
    <h2>{{pix}}</h2>
    <a href='/register'><button>Criar Conta</button></a>
    <a href='/login'><button>Login</button></a>
    </div>
    """,pix=PIX_KEY)

# ===== REGISTER =====

@app.route("/register",methods=["GET","POST"])
def register():

    if request.method=="POST":
        con=db()
        cur=con.cursor()
        cur.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",
        (request.form["username"],request.form["email"],request.form["password"]))
        con.commit()
        con.close()
        return redirect("/login")

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Registro</h2>
    <form method='post'>
    <input name='username' placeholder='Nome'>
    <input name='email' placeholder='Email'>
    <input name='password' placeholder='Senha'>
    <button>Criar Conta</button>
    </form>
    </div>
    """)

# ===== LOGIN =====

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":
        con=db()
        cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
        (request.form["email"],request.form["password"]))
        user=cur.fetchone()
        con.close()

        if user:
            session["user"]=user["id"]
            return redirect("/dashboard")

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Login</h2>
    <form method='post'>
    <input name='email'>
    <input name='password'>
    <button>Entrar</button>
    </form>
    </div>
    """)

# ===== DASHBOARD USER =====

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    con=db()
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (session["user"],))
    user=cur.fetchone()
    con.close()

    if user["approved"]==1:
        return render_template_string(STYLE+"""
        <div class='card'>
        <h2>✅ Compra aprovada</h2>
        <p>KEY enviada para seu email.</p>
        <a href='/bot'><button>Configurar Meu Bot</button></a>
        </div>
        """)

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Enviar Comprovante</h2>
    <form action='/send_proof' method='post' enctype='multipart/form-data'>
    <select name='plano'>
      <option>1 dia</option>
      <option>7 dias</option>
      <option>30 dias</option>
    </select>
    <input type='file' name='proof'>
    <button>Enviar</button>
    </form>
    </div>
    """)

# ===== SEND PROOF =====

@app.route("/send_proof",methods=["POST"])
def send_proof():

    uid=session["user"]
    file=request.files["proof"]

    filename=file.filename
    file.save(os.path.join(UPLOAD_FOLDER,filename))

    con=db()
    cur=con.cursor()

    cur.execute("INSERT INTO payments(user_id,plano,proof) VALUES(?,?,?)",
    (uid,request.form["plano"],filename))

    con.commit()
    con.close()

    return redirect("/dashboard")

# ===== ADMIN LOGIN =====

@app.route("/admin_login",methods=["GET","POST"])
def admin_login():

    if request.method=="POST":
        if request.form["user"]==ADMIN_USER and request.form["pass"]==ADMIN_PASS:
            session["admin"]=True
            return redirect(ADMIN_URL)

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>🔒 Login Admin</h2>
    <form method='post'>
    <input name='user'>
    <input name='pass'>
    <button>Entrar</button>
    </form>
    </div>
    """)

# ===== ADMIN PANEL (SECRET) =====

@app.route(ADMIN_URL)
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    con=db()
    cur=con.cursor()
    cur.execute("SELECT * FROM payments WHERE status='pendente'")
    pays=cur.fetchall()

    html="<h2>Painel Admin</h2>"

    for p in pays:
        html+=f"""
        <div class='card'>
        Plano: {p['plano']}<br>
        <img src='/uploads/{p['proof']}'><br>
        <a href='/approve/{p['id']}'><button>Aprovar</button></a>
        </div>
        """

    con.close()

    return render_template_string(STYLE+html)

# ===== VIEW IMAGE =====

@app.route("/uploads/<file>")
def uploads(file):
    return app.send_static_file("../uploads/"+file)

# ===== APPROVE =====

@app.route("/approve/<int:id>")
def approve(id):

    con=db()
    cur=con.cursor()

    cur.execute("SELECT user_id FROM payments WHERE id=?", (id,))
    uid=cur.fetchone()["user_id"]

    key=make_key()

    cur.execute("UPDATE users SET approved=1,key=? WHERE id=?", (key,uid))
    cur.execute("UPDATE payments SET status='aprovado' WHERE id=?", (id,))

    cur.execute("SELECT email FROM users WHERE id=?", (uid,))
    email=cur.fetchone()["email"]

    send_email(email,key)

    con.commit()
    con.close()

    return redirect(ADMIN_URL)

# ===== BOT PANEL =====

@app.route("/bot",methods=["GET","POST"])
def bot():

    if "user" not in session:
        return redirect("/login")

    if request.method=="POST":
        con=db()
        cur=con.cursor()
        cur.execute("UPDATE users SET bot_token=? WHERE id=?",
        (request.form["token"],session["user"]))
        con.commit()
        con.close()

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>🤖 Meu Bot</h2>
    <p>Pegue o TOKEN no Discord Developer Portal.</p>
    <form method='post'>
    <input name='token' placeholder='TOKEN DO BOT'>
    <button>Salvar</button>
    </form>
    </div>
    """)

# ===== START =====

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
