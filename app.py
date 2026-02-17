from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os, random, string, smtplib

app = Flask(__name__)
app.secret_key = "super_secret"

# ===== CONFIG =====
PIX_KEY = "SUA_CHAVE_PIX"
ADMIN_USER = "admin"
ADMIN_PASS = "123"

EMAIL = "SEUEMAIL@gmail.com"
EMAIL_PASS = "SENHA_APP"

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

# ===== DATABASE =====

def db():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        approved INTEGER DEFAULT 0,
        user_key TEXT
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

init_db()

# ===== HELPERS =====

def make_key():
    return ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(12))

def send_email(dest,key):
    try:
        msg=f"""Subject: SUA KEY

Compra aprovada!

KEY:
{key}
"""
        s=smtplib.SMTP("smtp.gmail.com",587)
        s.starttls()
        s.login(EMAIL,EMAIL_PASS)
        s.sendmail(EMAIL,dest,msg)
        s.quit()
    except:
        print("erro email")

# ===== DESIGN INSANO =====

STYLE = """
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial;}
body{
background:linear-gradient(135deg,#0d1117,#111827,#0f172a);
min-height:100vh;
display:flex;
justify-content:center;
align-items:flex-start;
padding:20px;
color:white;
}
.card{
background:rgba(20,20,35,.9);
backdrop-filter:blur(10px);
padding:30px;
border-radius:18px;
box-shadow:0 0 40px rgba(0,0,0,.6);
width:95%;
max-width:420px;
margin-top:20px;
animation:fade .4s ease;
}
h1,h2{margin-bottom:15px;}
input,select{
width:100%;
padding:12px;
margin:8px 0;
border:none;
border-radius:10px;
background:#0b0f1a;
color:white;
}
button{
width:100%;
padding:12px;
border:none;
border-radius:10px;
background:linear-gradient(90deg,#5865f2,#7289da);
color:white;
font-weight:bold;
margin-top:10px;
cursor:pointer;
transition:.3s;
}
button:hover{transform:scale(1.02);}
img{max-width:100%;border-radius:10px;}
a{text-decoration:none;}
@keyframes fade{
from{opacity:0;transform:translateY(20px);}
to{opacity:1;transform:translateY(0);}
}
</style>
"""

# ===== HOME =====

@app.route("/")
def home():
    return render_template_string(STYLE+"""
    <div class='card'>
    <h1>🔥 Loja Oficial</h1>
    <p>Pague via PIX:</p>
    <h2>{{pix}}</h2>
    <a href='/register'><button>Criar Conta</button></a>
    <a href='/login'><button>Login</button></a>
    </div>
    """,pix=PIX_KEY)

# ===== REGISTER =====

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        con=db(); cur=con.cursor()
        cur.execute("INSERT INTO users(username,email,password) VALUES(?,?,?)",
        (request.form["u"],request.form["e"],request.form["p"]))
        con.commit(); con.close()
        return redirect("/login")

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Registro</h2>
    <form method='post'>
    <input name='u' placeholder='Nome'>
    <input name='e' placeholder='Email'>
    <input name='p' placeholder='Senha'>
    <button>Registrar</button>
    </form>
    </div>
    """)

# ===== LOGIN =====

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db(); cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
        (request.form["e"],request.form["p"]))
        u=cur.fetchone(); con.close()
        if u:
            session["user"]=u["id"]
            return redirect("/dashboard")

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Login</h2>
    <form method='post'>
    <input name='e' placeholder='Email'>
    <input name='p' placeholder='Senha'>
    <button>Entrar</button>
    </form>
    </div>
    """)

# ===== USER PANEL =====

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    con=db(); cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (session["user"],))
    u=cur.fetchone(); con.close()

    if u["approved"]==1:
        return render_template_string(STYLE+"""
        <div class='card'>
        <h2>✅ Aprovado</h2>
        <p>Sua KEY foi enviada por EMAIL.</p>
        <button onclick="alert('Aqui depois vai config do bot')">Configurar Bot</button>
        </div>
        """)

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Enviar Comprovante</h2>
    <form action='/send' method='post' enctype='multipart/form-data'>
    <select name='plano'>
      <option>1 dia</option>
      <option>7 dias</option>
      <option>30 dias</option>
    </select>
    <input type='file' name='img'>
    <button>Enviar</button>
    </form>
    </div>
    """)

# ===== SEND PROOF =====

@app.route("/send",methods=["POST"])
def send():

    f=request.files["img"]
    name=f.filename
    f.save(os.path.join(UPLOAD_FOLDER,name))

    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO payments(user_id,plano,proof) VALUES(?,?,?)",
    (session["user"],request.form["plano"],name))
    con.commit(); con.close()

    return redirect("/dashboard")

# ===== ADMIN LOGIN =====

@app.route("/admin_login",methods=["GET","POST"])
def admin_login():

    if request.method=="POST":
        if request.form["u"]==ADMIN_USER and request.form["p"]==ADMIN_PASS:
            session["admin"]=True
            return redirect("/painel_admin_hidden")

    return render_template_string(STYLE+"""
    <div class='card'>
    <h2>Admin Login</h2>
    <form method='post'>
    <input name='u'>
    <input name='p'>
    <button>Entrar</button>
    </form>
    </div>
    """)

# ===== ADMIN PANEL =====

@app.route("/painel_admin_hidden")
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    con=db(); cur=con.cursor()
    cur.execute("SELECT * FROM payments WHERE status='pendente'")
    pays=cur.fetchall()

    html="<h2>PAINEL ADMIN</h2>"

    for p in pays:
        html += f"""
        <div class='card'>
        Plano: {p['plano']}<br>
        <img src='/uploads/{p['proof']}'><br>
        <a href='/approve/{p['id']}'><button>Aprovar</button></a>
        </div>
        """

    con.close()
    return render_template_string(STYLE+html)

@app.route("/uploads/<file>")
def up(file):
    return app.send_static_file("../uploads/"+file)

# ===== APPROVE =====

@app.route("/approve/<int:i>")
def approve(i):

    con=db(); cur=con.cursor()

    cur.execute("SELECT user_id FROM payments WHERE id=?", (i,))
    uid=cur.fetchone()["user_id"]

    key=make_key()

    cur.execute("UPDATE users SET approved=1,user_key=? WHERE id=?",(key,uid))
    cur.execute("UPDATE payments SET status='aprovado' WHERE id=?", (i,))

    cur.execute("SELECT email FROM users WHERE id=?", (uid,))
    email=cur.fetchone()["email"]

    send_email(email,key)

    con.commit(); con.close()

    return redirect("/painel_admin_hidden")

# ===== START =====

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
