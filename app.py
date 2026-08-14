import os
import sys
import re
import io
import json
import logging
import secrets
from flask import Flask, render_template_string, request, redirect, url_for, session
from decimal import Decimal
from contextlib import redirect_stdout
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import bank_app

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

HOST = '127.0.0.1'
PORT = 5000

def cli_log(tag, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO":"\033[94m","OK":"\033[92m","WARN":"\033[93m","ERROR":"\033[91m","EVENT":"\033[95m","DB":"\033[96m"}
    reset = "\033[0m"
    print(f"  [{ts}] {colors.get(tag,'')}{f'[{tag}]'}{reset} {msg}", flush=True)

def run_bank_func(func, input_map, *args):
    import builtins
    _real = builtins.input
    builtins.input = lambda prompt="": input_map.get(prompt, "")
    f = io.StringIO()
    try:
        with redirect_stdout(f):
            func(*args)
    finally:
        builtins.input = _real
    return f.getvalue()

_CSS = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--blue:#1a6bcc;--blue-dk:#0f4d99;--green:#1a7a3a;--red:#b02a2a;--bg:#eef2f7;--card:#fff;--text:#2c3e50;--muted:#6b7a8d;--border:#d8e0ea;--radius:10px;--shadow:0 2px 12px rgba(0,0,0,.09)}
body{font-family:'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:32px 16px 60px}
.page{width:100%;max-width:540px}.page.wide{max-width:880px}
.header{text-align:center;margin-bottom:26px}
.header .logo{font-size:2.6rem;margin-bottom:4px}
.header h1{font-size:1.5rem;color:var(--blue-dk);letter-spacing:-.3px}
.header p{color:var(--muted);font-size:.87rem;margin-top:4px}
.card{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:24px 26px;margin-bottom:18px}
.card-title{font-size:1rem;font-weight:700;color:var(--blue);margin-bottom:16px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border);padding-bottom:11px}
.menu-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.menu-btn{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:24px 10px;background:var(--card);border:2px solid var(--border);border-radius:var(--radius);cursor:pointer;text-decoration:none;color:var(--text);box-shadow:var(--shadow);transition:border-color .15s,box-shadow .15s,transform .1s}
.menu-btn:hover{border-color:var(--blue);box-shadow:0 6px 20px rgba(26,107,204,.15);transform:translateY(-2px)}
.menu-btn .icon{font-size:2.2rem}.menu-btn .label{font-size:.92rem;font-weight:700;color:var(--blue-dk)}.menu-btn .sub{font-size:.74rem;color:var(--muted);text-align:center}
.menu-btn.danger{border-color:#f5c6cb}.menu-btn.danger:hover{border-color:var(--red);box-shadow:0 6px 20px rgba(176,42,42,.12)}.menu-btn.danger .label{color:var(--red)}
.menu-btn.full{grid-column:span 2;padding:15px;flex-direction:row;justify-content:center;gap:10px}.menu-btn.full .icon{font-size:1.4rem}
.form-group{margin-bottom:13px}
.form-group label{display:block;font-size:.77rem;font-weight:700;color:var(--muted);margin-bottom:5px;text-transform:uppercase;letter-spacing:.05em}
.form-group input{width:100%;padding:10px 13px;border:1.5px solid var(--border);border-radius:7px;font-size:.94rem;color:var(--text);background:#f8fafc;transition:border-color .15s,box-shadow .15s;outline:none}
.form-group input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(26,107,204,.12);background:#fff}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:11px 20px;border-radius:7px;font-size:.93rem;font-weight:700;cursor:pointer;border:none;text-decoration:none;transition:all .15s;width:100%;margin-top:8px}
.btn-primary{background:var(--blue);color:#fff}.btn-primary:hover{background:var(--blue-dk)}
.btn-danger{background:var(--red);color:#fff}.btn-danger:hover{background:#8b1f1f}
.btn-ghost{background:transparent;color:var(--blue);border:1.5px solid var(--border);font-size:.84rem;padding:8px 16px;margin-top:0;width:auto}.btn-ghost:hover{border-color:var(--blue);background:#f0f5ff}
.alert{padding:12px 15px;border-radius:8px;margin-bottom:15px;font-size:.87rem;display:flex;align-items:flex-start;gap:9px}
.alert-success{background:#e6f4ec;border:1px solid #a8d5b8;color:#155724}
.alert-error{background:#fce8e8;border:1px solid #f5b8b8;color:#7a1f1f}
.alert-icon{font-size:1rem;flex-shrink:0;margin-top:1px}
.topbar{background:var(--blue-dk);color:#fff;border-radius:var(--radius);padding:13px 18px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;gap:12px;box-shadow:var(--shadow)}
.topbar .acc-info{display:flex;flex-direction:column}.topbar .acc-label{font-size:.7rem;opacity:.6}.topbar .acc-no{font-size:.86rem;font-weight:700;letter-spacing:.5px}.topbar .acc-name-large{font-size:.98rem;font-weight:700}
.topbar .bal{text-align:right}.topbar .bal-label{font-size:.68rem;opacity:.6}.topbar .bal-val{font-size:1.22rem;font-weight:800;color:#7fffb0}
.logout-btn{background:rgba(255,255,255,.15);border:none;color:#fff;border-radius:6px;padding:7px 13px;cursor:pointer;font-size:.8rem;font-weight:700;transition:background .15s;text-decoration:none;display:inline-block}.logout-btn:hover{background:rgba(255,255,255,.28)}
.action-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:11px;margin-bottom:16px}
.ac{background:var(--card);border-radius:var(--radius);padding:17px 9px;box-shadow:var(--shadow);cursor:pointer;border:2px solid transparent;text-decoration:none;color:var(--text);display:flex;flex-direction:column;align-items:center;gap:7px;transition:border-color .15s,transform .1s,box-shadow .15s}
.ac:hover{border-color:var(--blue);transform:translateY(-2px);box-shadow:0 6px 20px rgba(26,107,204,.13)}.ac.red:hover{border-color:var(--red);box-shadow:0 6px 20px rgba(176,42,42,.13)}
.ac .ac-icon{font-size:1.65rem}.ac .ac-lbl{font-size:.76rem;font-weight:700;color:var(--blue-dk);text-align:center;line-height:1.3}.ac.red .ac-lbl{color:var(--red)}.ac.full-w{grid-column:span 3}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200;align-items:center;justify-content:center;padding:16px}.overlay.open{display:flex}
.modal{background:var(--card);border-radius:14px;padding:26px 26px 20px;width:100%;max-width:420px;box-shadow:0 8px 40px rgba(0,0,0,.22);position:relative}
.modal-title{font-size:1.02rem;font-weight:700;color:var(--blue);margin-bottom:16px}
.modal-close{position:absolute;top:13px;right:15px;background:none;border:none;font-size:1.3rem;cursor:pointer;color:var(--muted)}.modal-close:hover{color:var(--text)}
.stat-row{display:flex;gap:11px;margin-bottom:16px;flex-wrap:wrap}
.stat{flex:1;min-width:105px;background:var(--card);border-radius:var(--radius);padding:13px 15px;box-shadow:var(--shadow)}
.stat .s-label{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}.stat .s-val{font-size:1.2rem;font-weight:800;margin-top:3px}
.s-green{color:var(--green)}.s-red{color:var(--red)}.s-blue{color:var(--blue)}
.tbl-wrap{overflow-x:auto;border-radius:8px;box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;background:var(--card)}
thead th{background:var(--blue);color:#fff;padding:10px 13px;text-align:left;font-size:.8rem}
tbody td{padding:9px 13px;border-bottom:1px solid var(--border);font-size:.84rem}
tbody tr:last-child td{border-bottom:none}tbody tr:hover td{background:#f0f5ff}
.badge{padding:3px 9px;border-radius:20px;font-size:.73rem;font-weight:700}
.badge-dep{background:#e6f4ec;color:#155724}.badge-wit{background:#fce8e8;color:#7a1f1f}
.tx-dep{color:var(--green);font-weight:700}.tx-wit{color:var(--red);font-weight:700}
.iv-bar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.iv-btn{padding:7px 18px;border-radius:20px;border:2px solid var(--border);background:#fff;color:var(--blue);font-weight:700;font-size:.81rem;cursor:pointer;transition:all .15s;text-decoration:none}.iv-btn:hover{border-color:var(--blue)}.iv-btn.active{background:var(--blue);color:#fff;border-color:var(--blue)}
.result{border-radius:var(--radius);padding:20px 18px;text-align:center;margin-bottom:16px}
.result.ok{background:#e6f4ec;border:1.5px solid #a8d5b8}.result.fail{background:#fce8e8;border:1.5px solid #f5b8b8}
.result .r-icon{font-size:2.1rem;margin-bottom:7px}.result .r-title{font-size:1.02rem;font-weight:700}.result .r-detail{font-size:.86rem;color:var(--muted);margin-top:5px}
.acc-no-badge{display:inline-block;background:var(--blue);color:#fff;border-radius:8px;padding:8px 18px;font-size:1.18rem;font-weight:800;letter-spacing:3px;margin:10px 0}
.back{display:inline-flex;align-items:center;gap:5px;color:var(--blue);text-decoration:none;font-size:.84rem;font-weight:700;margin-bottom:16px}.back:hover{text-decoration:underline}
.empty{text-align:center;padding:42px 16px;color:var(--muted)}.empty .e-icon{font-size:2.5rem;margin-bottom:10px}.empty p{font-size:.9rem}
@media(max-width:480px){.action-grid{grid-template-columns:1fr 1fr}.ac.full-w{grid-column:span 2}.form-row{grid-template-columns:1fr}.menu-grid{grid-template-columns:1fr 1fr}}
</style>
"""

def page(title, body, wide=False):
    return f"""<!doctype html><html lang="en"><head><title>{title} — Bank App</title>{_CSS}</head><body><div class="page {'wide' if wide else ''}">{body}</div></body></html>"""

def alert_html(msg, kind="success"):
    icon = "✅" if kind == "success" else "❌"
    return f'<div class="alert alert-{kind}"><span class="alert-icon">{icon}</span><span>{msg}</span></div>'

def header(title, subtitle=""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    return f'<div class="header"><div class="logo">🏦</div><h1>{title}</h1>{sub}</div>'

# ── MAIN MENU ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    msg = session.pop('flash', None)
    flash_html = ""
    if msg:
        kind = "error" if any(w in msg for w in ["Error","error","❌","fail","Invalid"]) else "success"
        flash_html = alert_html(msg, kind)
    body = header("Bank App", "Your trusted local banking system") + flash_html + """
<div class="card">
  <div class="card-title">🏠 Main Menu</div>
  <div class="menu-grid">
    <a href="/new_account" class="menu-btn">
      <span class="icon">📝</span>
      <span class="label">Open Account</span>
      <span class="sub">Create a new bank account</span>
    </a>
    <a href="/account_login" class="menu-btn">
      <span class="icon">🔐</span>
      <span class="label">Account Login</span>
      <span class="sub">Access your account</span>
    </a>
    <a href="/close_account_page" class="menu-btn danger">
      <span class="icon">🗑️</span>
      <span class="label">Close Account</span>
      <span class="sub">Permanently close an account</span>
    </a>
    <a href="/exit" class="menu-btn full danger" onclick="return confirm('Exit the application?')">
      <span class="icon">⏻</span>
      <span class="label">Exit</span>
    </a>
  </div>
</div>"""
    return page("Main Menu", body)

# ── OPEN NEW ACCOUNT ──────────────────────────────────────────────────────
@app.route('/new_account', methods=['GET','POST'])
def new_account_page():
    if request.method == 'GET':
        body = (header("Open New Account") +
            '<a href="/" class="back">← Main Menu</a>' + """
<div class="card">
  <div class="card-title">📝 Personal Details</div>
  <form method="POST" action="/new_account">
    <div class="form-row">
      <div class="form-group"><label>Full Name *</label>
        <input type="text" name="name" placeholder="e.g. Debanjan Mistry" required></div>
      <div class="form-group"><label>Date of Birth *</label>
        <input type="date" name="dob" required></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Father's Name</label>
        <input type="text" name="father_name" placeholder="Father's full name"></div>
      <div class="form-group"><label>Mother's Name</label>
        <input type="text" name="mother_name" placeholder="Mother's full name"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Phone</label>
        <input type="text" name="phone" placeholder="+91 XXXXX XXXXX"></div>
      <div class="form-group"><label>Email</label>
        <input type="email" name="email" placeholder="you@email.com"></div>
    </div>
    <div class="form-group"><label>Address</label>
      <input type="text" name="address" placeholder="Street, City, State"></div>
    <div class="form-row">
      <div class="form-group"><label>Aadhar Number *</label>
        <input type="text" name="aadhar" placeholder="12-digit Aadhar" required></div>
      <div class="form-group"><label>4-Digit PIN *</label>
        <input type="password" name="pin" pattern="[0-9]{4}" maxlength="4" placeholder="••••" required></div>
    </div>
    <button type="submit" class="btn btn-primary">✅ Open Account</button>
  </form>
</div>""")
        return page("Open Account", body)

    name=request.form['name']; father_name=request.form.get('father_name','')
    mother_name=request.form.get('mother_name',''); phone=request.form.get('phone','')
    email=request.form.get('email',''); address=request.form.get('address','')
    aadhar=request.form['aadhar']; dob_str=request.form['dob']; pin=request.form['pin']
    input_map={"Enter Name: ":name,"Enter Father Name: ":father_name,"Enter Mother Name: ":mother_name,
               "Enter Phone No: ":phone,"Enter Email ID: ":email,"Enter Address: ":address,
               "Enter Aadhar No: ":aadhar,"Enter DOB (YYYY-MM-DD): ":dob_str,"Create 4-digit PIN: ":pin}
    if bank_app.connect_db():
        try:
            output = run_bank_func(bank_app.open_new_account, input_map)
            if "Account opened successfully!" in output:
                m = re.search(r"Account No: (\d+)", output)
                acc_no = m.group(1) if m else "N/A"
                cli_log("EVENT", f"🆕 NEW ACCOUNT — Name: {name} | Account No: {acc_no}")
                result_html = f'<div class="result ok"><div class="r-icon">🎉</div><div class="r-title">Account Opened Successfully!</div><div class="r-detail">Your new account number is</div><div class="acc-no-badge">{acc_no}</div><div class="r-detail">Please save this number. Use it with your PIN to login.</div></div>'
            else:
                msg = output.strip().replace("\n--- Open New Account ---","").strip()
                cli_log("WARN", f"Account creation failed for {name}: {msg}")
                result_html = f'<div class="result fail"><div class="r-icon">⚠️</div><div class="r-title">Could Not Open Account</div><div class="r-detail">{msg}</div></div>'
        except Exception as e:
            cli_log("ERROR", f"Open account exception: {e}")
            result_html = f'<div class="result fail"><div class="r-icon">⚠️</div><div class="r-title">Error</div><div class="r-detail">{e}</div></div>'
        finally: bank_app.close_db()
    else:
        result_html = '<div class="result fail"><div class="r-icon">⚠️</div><div class="r-title">Database Connection Failed</div><div class="r-detail">Ensure MySQL is running.</div></div>'
        cli_log("ERROR","DB connection failed.")
    body = (header("Open New Account") + '<a href="/" class="back">← Main Menu</a>' + result_html +
            '<a href="/new_account" class="btn btn-primary" style="display:inline-flex;width:auto;padding:10px 20px;text-decoration:none;margin-right:10px;">Open Another Account</a>'
            + '<a href="/" class="btn btn-ghost" style="margin-top:8px;">Back to Main Menu</a>')
    return page("Open Account", body)

# ── ACCOUNT LOGIN ─────────────────────────────────────────────────────────
@app.route('/account_login', methods=['GET','POST'])
def account_login_page():
    if session.get('acc_no'): return redirect(url_for('dashboard'))
    if request.method == 'GET':
        body = (header("Account Login") + '<a href="/" class="back">← Main Menu</a>' + """
<div class="card">
  <div class="card-title">🔐 Login to Your Account</div>
  <form method="POST" action="/account_login">
    <div class="form-group"><label>Account Number</label>
      <input type="number" name="acc_no" placeholder="12-digit account number" required></div>
    <div class="form-group"><label>4-Digit PIN</label>
      <input type="password" name="pin" maxlength="4" placeholder="••••" required></div>
    <button type="submit" class="btn btn-primary">🔐 Login</button>
  </form>
</div>""")
        return page("Login", body)
    acc_no=request.form['acc_no']; pin=request.form['pin']
    if bank_app.connect_db():
        try:
            bank_app.cursor.execute("SELECT name,balance FROM customers WHERE account_no=%s AND pin=%s",(acc_no,pin))
            result = bank_app.cursor.fetchone()
            if result:
                session['acc_no']=acc_no; session['acc_name']=result[0]; session['balance']=float(result[1])
                cli_log("EVENT",f"🔐 LOGIN — Account: {acc_no} | Name: {result[0]}")
                bank_app.close_db(); return redirect(url_for('dashboard'))
            else:
                bank_app.close_db(); cli_log("WARN",f"Failed login: {acc_no}")
                body = (header("Account Login") + '<a href="/" class="back">← Main Menu</a>' +
                    alert_html("Invalid account number or PIN. Please try again.","error") + """
<div class="card">
  <div class="card-title">🔐 Login to Your Account</div>
  <form method="POST" action="/account_login">
    <div class="form-group"><label>Account Number</label>
      <input type="number" name="acc_no" placeholder="12-digit account number" required></div>
    <div class="form-group"><label>4-Digit PIN</label>
      <input type="password" name="pin" maxlength="4" placeholder="••••" required></div>
    <button type="submit" class="btn btn-primary">🔐 Login</button>
  </form>
</div>""")
                return page("Login", body)
        except Exception as e:
            bank_app.close_db(); cli_log("ERROR",f"Login exception: {e}")
    else: cli_log("ERROR","DB connection failed during login.")
    session['flash']="Error: Database connection failed."; return redirect(url_for('index'))

# ── DASHBOARD ─────────────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    if not session.get('acc_no'):
        session['flash']="Please login first."; return redirect(url_for('account_login_page'))
    acc_no=session['acc_no']; acc_name=session.get('acc_name','Account Holder')
    if bank_app.connect_db():
        try:
            bank_app.cursor.execute("SELECT balance FROM customers WHERE account_no=%s",(acc_no,))
            r=bank_app.cursor.fetchone()
            if r: session['balance']=float(r[0])
        except: pass
        finally: bank_app.close_db()
    balance=session.get('balance',0.0)
    flash_msg=session.pop('flash',None)
    flash_html=""
    if flash_msg:
        kind="error" if any(w in flash_msg for w in ["Error","error","❌","fail","Invalid"]) else "success"
        flash_html=alert_html(flash_msg,kind)
    topbar=f"""
<div class="topbar">
  <div class="acc-info">
    <span class="acc-label">Logged in as</span>
    <span class="acc-name-large">{acc_name}</span>
    <span class="acc-no">Acc: {acc_no}</span>
  </div>
  <div class="bal"><div class="bal-label">BALANCE</div><div class="bal-val">${balance:,.2f}</div></div>
  <a href="/logout" class="logout-btn">Logout</a>
</div>"""
    modals=f"""
<div class="overlay" id="m-deposit">
  <div class="modal"><button class="modal-close" onclick="closeModal('m-deposit')">✕</button>
    <div class="modal-title">💰 Deposit</div>
    <form method="POST" action="/deposit">
      <input type="hidden" name="acc_no" value="{acc_no}">
      <div class="form-group"><label>Amount</label><input type="number" step="0.01" min="0.01" name="amount" placeholder="0.00" required></div>
      <button type="submit" class="btn btn-primary">Confirm Deposit</button>
    </form></div></div>
<div class="overlay" id="m-withdraw">
  <div class="modal"><button class="modal-close" onclick="closeModal('m-withdraw')">✕</button>
    <div class="modal-title">🏧 Withdraw</div>
    <form method="POST" action="/withdraw">
      <input type="hidden" name="acc_no" value="{acc_no}">
      <div class="form-group"><label>Amount</label><input type="number" step="0.01" min="0.01" name="amount" placeholder="0.00" required></div>
      <button type="submit" class="btn btn-primary">Confirm Withdrawal</button>
    </form></div></div>
<div class="overlay" id="m-transfer">
  <div class="modal"><button class="modal-close" onclick="closeModal('m-transfer')">✕</button>
    <div class="modal-title">🔄 Transfer Funds</div>
    <form method="POST" action="/transfer">
      <input type="hidden" name="acc_no" value="{acc_no}">
      <div class="form-group"><label>Destination Account No</label><input type="number" name="dest_acc_no" placeholder="12-digit account number" required></div>
      <div class="form-group"><label>Amount</label><input type="number" step="0.01" min="0.01" name="amount" placeholder="0.00" required></div>
      <button type="submit" class="btn btn-primary">Confirm Transfer</button>
    </form></div></div>
<div class="overlay" id="m-pin">
  <div class="modal"><button class="modal-close" onclick="closeModal('m-pin')">✕</button>
    <div class="modal-title">🔑 Change PIN</div>
    <form method="POST" action="/change_pin">
      <input type="hidden" name="acc_no" value="{acc_no}">
      <div class="form-group"><label>Current PIN</label><input type="password" name="current_pin" maxlength="4" placeholder="••••" required></div>
      <div class="form-group"><label>New PIN (4 digits)</label><input type="password" name="new_pin" pattern="[0-9]{{4}}" maxlength="4" placeholder="••••" required></div>
      <button type="submit" class="btn btn-primary">Update PIN</button>
    </form></div></div>
<div class="overlay" id="m-close">
  <div class="modal"><button class="modal-close" onclick="closeModal('m-close')">✕</button>
    <div class="modal-title">⚠️ Close This Account</div>
    <p style="font-size:.85rem;color:var(--muted);margin-bottom:14px;">This will permanently delete your account. This cannot be undone.</p>
    <form method="POST" action="/close_account_action">
      <input type="hidden" name="acc_no" value="{acc_no}">
      <div class="form-group"><label>Confirm PIN</label><input type="password" name="pin" maxlength="4" placeholder="••••" required></div>
      <button type="submit" class="btn btn-danger">Permanently Close Account</button>
    </form></div></div>
<script>
function openModal(id){{document.getElementById(id).classList.add('open')}}
function closeModal(id){{document.getElementById(id).classList.remove('open')}}
document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',e=>{{if(e.target===o)o.classList.remove('open')}}))
</script>"""
    actions=f"""
<div class="card">
  <div class="card-title">⚡ Account Actions</div>
  <div class="action-grid">
    <a class="ac" href="#" onclick="openModal('m-deposit');return false"><span class="ac-icon">💰</span><span class="ac-lbl">Deposit</span></a>
    <a class="ac" href="#" onclick="openModal('m-withdraw');return false"><span class="ac-icon">🏧</span><span class="ac-lbl">Withdraw</span></a>
    <a class="ac" href="#" onclick="openModal('m-transfer');return false"><span class="ac-icon">🔄</span><span class="ac-lbl">Transfer</span></a>
    <a class="ac" href="#" onclick="openModal('m-pin');return false"><span class="ac-icon">🔑</span><span class="ac-lbl">Change PIN</span></a>
    <a class="ac" href="/history?acc_no={acc_no}"><span class="ac-icon">📋</span><span class="ac-lbl">Transaction History</span></a>
    <a class="ac" href="/charts?acc_no={acc_no}"><span class="ac-icon">📊</span><span class="ac-lbl">Charts</span></a>
    <a class="ac red full-w" href="#" onclick="openModal('m-close');return false"><span class="ac-icon">🗑️</span><span class="ac-lbl">Close This Account</span></a>
  </div>
</div>"""
    body = topbar + flash_html + actions + modals
    return page("Dashboard", body)

# ── CLOSE ACCOUNT (main menu) ─────────────────────────────────────────────
@app.route('/close_account_page', methods=['GET','POST'])
def close_account_page():
    if request.method == 'GET':
        body = (header("Close Account") + '<a href="/" class="back">← Main Menu</a>' + """
<div class="card">
  <div class="card-title">🗑️ Close Account</div>
  <p style="font-size:.86rem;color:var(--muted);margin-bottom:16px;">Enter your account number and PIN to permanently close the account. This <strong>cannot be undone</strong>.</p>
  <form method="POST" action="/close_account_page">
    <div class="form-group"><label>Account Number</label>
      <input type="number" name="acc_no" placeholder="12-digit account number" required></div>
    <div class="form-group"><label>PIN</label>
      <input type="password" name="pin" maxlength="4" placeholder="••••" required></div>
    <button type="submit" class="btn btn-danger">🗑️ Close Account</button>
  </form>
</div>""")
        return page("Close Account", body)
    acc_no_to_close=request.form['acc_no']; pin=request.form['pin']
    input_map={"Enter Account No: ":acc_no_to_close,"Enter PIN: ":pin}
    if bank_app.connect_db():
        try:
            output=run_bank_func(bank_app.close_account,input_map)
            if "Account closed successfully." in output:
                cli_log("EVENT",f"❌ ACCOUNT CLOSED — Account: {acc_no_to_close}")
                result_html=f'<div class="result ok"><div class="r-icon">✅</div><div class="r-title">Account Closed</div><div class="r-detail">Account <strong>{acc_no_to_close}</strong> has been permanently closed.</div></div>'
            else:
                msg=output.strip().replace("\n--- Close Account ---","").strip() or "Invalid account number or PIN."
                cli_log("WARN",f"Close failed for {acc_no_to_close}: {msg}")
                result_html=f'<div class="result fail"><div class="r-icon">⚠️</div><div class="r-title">Could Not Close Account</div><div class="r-detail">{msg}</div></div>'
        except Exception as e:
            cli_log("ERROR",f"Close account exception: {e}")
            result_html=f'<div class="result fail"><div class="r-icon">⚠️</div><div class="r-title">Error</div><div class="r-detail">{e}</div></div>'
        finally: bank_app.close_db()
    else:
        result_html='<div class="result fail"><div class="r-icon">⚠️</div><div class="r-title">Database Connection Failed</div></div>'
        cli_log("ERROR","DB connection failed.")
    body=(header("Close Account")+'<a href="/" class="back">← Main Menu</a>'+result_html+
          '<a href="/" class="btn btn-ghost" style="display:inline-flex;width:auto;">← Back to Main Menu</a>')
    return page("Close Account", body)

# ── ACTION ROUTES ─────────────────────────────────────────────────────────
def require_login():
    if not session.get('acc_no'):
        session['flash']="Please login first."; return False
    return True

@app.route('/deposit', methods=['POST'])
def deposit():
    if not require_login(): return redirect(url_for('account_login_page'))
    acc_no=session['acc_no']; amount=request.form['amount']
    if bank_app.connect_db():
        try:
            output=run_bank_func(bank_app.deposit,{"Enter amount to deposit: ":amount},acc_no)
            if "Successfully deposited" in output:
                m=re.search(r"New balance: \$?([\d.]+)",output)
                bal=m.group(1) if m else ""
                if bal: session['balance']=float(bal)
                session['flash']=f"✅ Deposited ${float(amount):,.2f}. New balance: ${float(bal):,.2f}" if bal else f"✅ Deposited ${float(amount):,.2f}."
                cli_log("EVENT",f"💰 DEPOSIT — Account: {acc_no} | ${amount}")
            else:
                msg=output.strip().replace("\n--- Deposit ---","").strip()
                session['flash']=f"Error: {msg}"; cli_log("WARN",f"Deposit issue: {msg}")
        except Exception as e: session['flash']=f"Error: {e}"; cli_log("ERROR",f"Deposit: {e}")
        finally: bank_app.close_db()
    else: session['flash']="Error: DB connection failed."
    return redirect(url_for('dashboard'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if not require_login(): return redirect(url_for('account_login_page'))
    acc_no=session['acc_no']; amount=request.form['amount']
    if bank_app.connect_db():
        try:
            output=run_bank_func(bank_app.withdraw,{"Enter amount to withdraw: ":amount},acc_no)
            if "Successfully withdrew" in output:
                m=re.search(r"New balance: \$?([\d.]+)",output)
                bal=m.group(1) if m else ""
                if bal: session['balance']=float(bal)
                session['flash']=f"✅ Withdrew ${float(amount):,.2f}. New balance: ${float(bal):,.2f}" if bal else f"✅ Withdrew ${float(amount):,.2f}."
                cli_log("EVENT",f"🏧 WITHDRAW — Account: {acc_no} | ${amount}")
            else:
                msg=output.strip().replace("\n--- Withdraw ---","").strip()
                session['flash']=f"Error: {msg}"; cli_log("WARN",f"Withdraw issue: {msg}")
        except Exception as e: session['flash']=f"Error: {e}"; cli_log("ERROR",f"Withdraw: {e}")
        finally: bank_app.close_db()
    else: session['flash']="Error: DB connection failed."
    return redirect(url_for('dashboard'))

@app.route('/transfer', methods=['POST'])
def transfer():
    if not require_login(): return redirect(url_for('account_login_page'))
    acc_no=session['acc_no']; dest=request.form['dest_acc_no']; amount=request.form['amount']
    input_map={"Enter destination account number: ":dest,"Enter amount to transfer: ":amount}
    if bank_app.connect_db():
        try:
            output=run_bank_func(bank_app.transfer,input_map,acc_no)
            if "Successfully transferred" in output:
                m=re.search(r"new balance: \$?([\d.]+)",output,re.IGNORECASE)
                bal=m.group(1) if m else ""
                if bal: session['balance']=float(bal)
                session['flash']=f"✅ Transferred ${float(amount):,.2f} to account {dest}."
                cli_log("EVENT",f"🔄 TRANSFER — {acc_no}→{dest} | ${amount}")
            else:
                msg=output.strip().replace("\n--- Transfer ---","").strip()
                session['flash']=f"Error: {msg}"; cli_log("WARN",f"Transfer issue: {msg}")
        except Exception as e: session['flash']=f"Error: {e}"; cli_log("ERROR",f"Transfer: {e}")
        finally: bank_app.close_db()
    else: session['flash']="Error: DB connection failed."
    return redirect(url_for('dashboard'))

@app.route('/change_pin', methods=['POST'])
def change_pin():
    if not require_login(): return redirect(url_for('account_login_page'))
    acc_no=session['acc_no']
    input_map={"Enter current 4-digit PIN: ":request.form['current_pin'],"Enter new 4-digit PIN: ":request.form['new_pin']}
    if bank_app.connect_db():
        try:
            output=run_bank_func(bank_app.change_pin,input_map,acc_no)
            if "PIN changed successfully" in output:
                session['flash']="✅ PIN changed successfully."; cli_log("EVENT",f"🔑 PIN CHANGED — {acc_no}")
            else:
                msg=output.strip().replace("\n--- Change PIN ---","").strip()
                session['flash']=f"Error: {msg}"; cli_log("WARN",f"PIN change issue: {msg}")
        except Exception as e: session['flash']=f"Error: {e}"; cli_log("ERROR",f"PIN change: {e}")
        finally: bank_app.close_db()
    else: session['flash']="Error: DB connection failed."
    return redirect(url_for('dashboard'))

@app.route('/close_account_action', methods=['POST'])
def close_account_action():
    if not require_login(): return redirect(url_for('account_login_page'))
    acc_no=session['acc_no']; pin=request.form['pin']
    input_map={"Enter Account No: ":str(acc_no),"Enter PIN: ":pin}
    if bank_app.connect_db():
        try:
            output=run_bank_func(bank_app.close_account,input_map)
            if "Account closed successfully." in output:
                cli_log("EVENT",f"❌ ACCOUNT CLOSED (dashboard) — {acc_no}")
                session.clear(); session['flash']=f"✅ Account {acc_no} permanently closed."
                bank_app.close_db(); return redirect(url_for('index'))
            else:
                msg=output.strip().replace("\n--- Close Account ---","").strip()
                session['flash']=f"Error: {msg}"; cli_log("WARN",f"Close issue: {msg}")
        except Exception as e: session['flash']=f"Error: {e}"; cli_log("ERROR",f"Close: {e}")
        finally: bank_app.close_db()
    else: session['flash']="Error: DB connection failed."
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    cli_log("EVENT",f"🚪 LOGOUT — Account: {session.get('acc_no','?')}")
    session.clear(); session['flash']="You have been logged out."
    return redirect(url_for('index'))

@app.route('/exit')
def exit_app():
    session.clear()
    cli_log("INFO","Exit selected — returning to main menu.")
    session['flash'] = "You have exited. Welcome back!"
    return redirect(url_for('index'))

# ── HISTORY ───────────────────────────────────────────────────────────────
@app.route('/history')
def history():
    if not session.get('acc_no'):
        session['flash']="Please login first."; return redirect(url_for('account_login_page'))
    acc_no=request.args.get('acc_no') or session['acc_no']
    records=[]; total_dep=Decimal('0.00'); total_wit=Decimal('0.00')
    if bank_app.connect_db():
        try:
            raw=bank_app.get_transaction_history(acc_no)
            for row in raw:
                amount,ts,tx_type=row
                records.append({'amount':amount,'time':ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts,'strftime') else str(ts),'type':tx_type})
                if tx_type=='deposit': total_dep+=Decimal(str(amount))
                else: total_wit+=Decimal(str(amount))
            cli_log("EVENT",f"📋 HISTORY — Account: {acc_no} | {len(records)} records")
        except Exception as e: cli_log("ERROR",f"History: {e}")
        finally: bank_app.close_db()
    stat_row=f"""<div class="stat-row">
  <div class="stat"><div class="s-label">Total Deposited</div><div class="s-val s-green">+${total_dep:.2f}</div></div>
  <div class="stat"><div class="s-label">Total Withdrawn</div><div class="s-val s-red">-${total_wit:.2f}</div></div>
  <div class="stat"><div class="s-label">Transactions</div><div class="s-val s-blue">{len(records)}</div></div>
</div>"""
    if records:
        rows_html="".join(
            f"<tr><td>{i}</td><td><span class='badge {'badge-dep' if r['type']=='deposit' else 'badge-wit'}'>"
            f"{'DEPOSIT' if r['type']=='deposit' else 'WITHDRAW'}</span></td>"
            f"<td class='{'tx-dep' if r['type']=='deposit' else 'tx-wit'}'>"
            f"{'+' if r['type']=='deposit' else '-'}${float(r['amount']):,.2f}</td><td>{r['time']}</td></tr>"
            for i,r in enumerate(records,1))
        table_html=f'<div class="tbl-wrap"><table><thead><tr><th>#</th><th>Type</th><th>Amount</th><th>Date &amp; Time</th></tr></thead><tbody>{rows_html}</tbody></table></div>'
    else:
        table_html='<div class="empty"><div class="e-icon">📭</div><p>No transactions found yet.</p></div>'
    body=(header("Transaction History")+f'<a href="/dashboard" class="back">← Dashboard</a>'
          +f'<p style="color:var(--muted);font-size:.83rem;margin-bottom:12px;">Account: <strong>{acc_no}</strong></p>'
          +stat_row+table_html)
    return page("Transaction History", body, wide=True)

# ── CHARTS ────────────────────────────────────────────────────────────────
@app.route('/charts')
def charts():
    if not session.get('acc_no'):
        session['flash']="Please login first."; return redirect(url_for('account_login_page'))
    acc_no=request.args.get('acc_no') or session['acc_no']
    interval=request.args.get('interval','day')
    if interval not in ('day','month','year'): interval='day'
    iv_labels={'day':'Per Day','month':'Per Month','year':'Per Year'}
    labels=[]; deps=[]; wits=[]; total_dep=total_wit=0.0
    if bank_app.connect_db():
        try:
            rows=bank_app.get_chart_data(acc_no,interval)
            for row in rows:
                labels.append(row['label']); deps.append(row['deposit']); wits.append(row['withdraw'])
                total_dep+=row['deposit']; total_wit+=row['withdraw']
            cli_log("EVENT",f"📊 CHARTS — Account: {acc_no} | {interval} | {len(labels)} periods")
        except Exception as e: cli_log("ERROR",f"Chart data: {e}")
        finally: bank_app.close_db()
    net=total_dep-total_wit
    iv_bar="".join(f'<a href="/charts?acc_no={acc_no}&interval={iv}" class="iv-btn {"active" if interval==iv else ""}">{lbl}</a>' for iv,lbl in iv_labels.items())
    stat_row=f"""<div class="stat-row">
  <div class="stat"><div class="s-label">Total Deposited</div><div class="s-val s-green">+${total_dep:,.2f}</div></div>
  <div class="stat"><div class="s-label">Total Withdrawn</div><div class="s-val s-red">-${total_wit:,.2f}</div></div>
  <div class="stat"><div class="s-label">Net Flow</div><div class="s-val {'s-green' if net>=0 else 's-red'}">{'+' if net>=0 else '-'}${abs(net):,.2f}</div></div>
  <div class="stat"><div class="s-label">Periods</div><div class="s-val s-blue">{len(labels)}</div></div>
</div>"""
    if labels:
        chart_section=f"""
<div class="card"><div class="card-title">📊 Deposits vs Withdrawals — {iv_labels[interval]}</div><canvas id="barChart" height="110"></canvas></div>
<div class="card"><div class="card-title">📈 Net Flow per Period</div><canvas id="netChart" height="80"></canvas></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
const labels={json.dumps(labels)},depData={json.dumps(deps)},witData={json.dumps(wits)};
const netData=labels.map((_,i)=>+(depData[i]-witData[i]).toFixed(2));
const fmtY=v=>'$'+v.toLocaleString(),tip=ctx=>' $'+ctx.parsed.y.toFixed(2);
new Chart(document.getElementById('barChart'),{{type:'bar',data:{{labels,datasets:[
  {{label:'Deposit',data:depData,backgroundColor:'rgba(40,167,69,.72)',borderColor:'#1a7a3a',borderWidth:1,borderRadius:5}},
  {{label:'Withdraw',data:witData,backgroundColor:'rgba(176,42,42,.72)',borderColor:'#8b1f1f',borderWidth:1,borderRadius:5}}
]}},options:{{responsive:true,plugins:{{legend:{{position:'top'}},tooltip:{{callbacks:{{label:tip}}}}}},scales:{{x:{{title:{{display:true,text:'Time Period',font:{{weight:'bold'}}}},grid:{{display:false}}}},y:{{title:{{display:true,text:'Amount ($)',font:{{weight:'bold'}}}},beginAtZero:true,ticks:{{callback:fmtY}}}}}}}}}});
new Chart(document.getElementById('netChart'),{{type:'line',data:{{labels,datasets:[{{label:'Net Flow',data:netData,borderColor:'#1a6bcc',backgroundColor:'rgba(26,107,204,.1)',borderWidth:2,pointRadius:4,fill:true,tension:.3,pointBackgroundColor:netData.map(v=>v>=0?'#1a7a3a':'#b02a2a')}}]}},options:{{responsive:true,plugins:{{legend:{{position:'top'}},tooltip:{{callbacks:{{label:ctx=>' Net: $'+ctx.parsed.y.toFixed(2)}}}}}},scales:{{x:{{title:{{display:true,text:'Time Period',font:{{weight:'bold'}}}},grid:{{display:false}}}},y:{{title:{{display:true,text:'Net ($)',font:{{weight:'bold'}}}},ticks:{{callback:fmtY}}}}}}}}}});</script>"""
    else:
        chart_section='<div class="empty"><div class="e-icon">📭</div><p>No transaction data yet. Make a deposit or withdrawal to see charts.</p></div>'
    body=(header("Transaction Charts")+f'<a href="/dashboard" class="back">← Dashboard</a>'
          +f'<p style="color:var(--muted);font-size:.83rem;margin-bottom:12px;">Account: <strong>{acc_no}</strong></p>'
          +f'<div class="iv-bar">{iv_bar}</div>'+stat_row+chart_section)
    return page("Charts", body, wide=True)

# ── STARTUP BANNER ────────────────────────────────────────────────────────
def print_banner():
    c,g,y,b,r="\033[96m","\033[92m","\033[93m","\033[1m","\033[0m"
    print(f"\n  {c}{'═'*54}{r}\n  {b}{c}   🏦  BANK APPLICATION — LOCAL SERVER{r}\n  {c}{'═'*54}{r}\n")
    print(f"  {g}  Webpage URL   :{r}  {b}http://{HOST}:{PORT}{r}")
    print(f"  {y}  Database Name :{r}  {b}{bank_app.DB_CONFIG['database']}{r}")
    print(f"  {y}  DB Host       :{r}  {b}{bank_app.DB_CONFIG['host']}{r}")
    print(f"  {y}  DB User       :{r}  {b}{bank_app.DB_CONFIG['user']}{r}")
    print(f"  {y}  DB Password   :{r}  {b}{bank_app.DB_CONFIG['password']}{r}")
    print(f"\n  {c}  ✅  Open the URL in your browser to use the app.{r}")
    print(f"  {c}  ⛔  Press Ctrl+C in this window to stop the server.{r}")
    print(f"\n  {c}{'─'*54}{r}\n  {'Timestamp':<12} {'Tag':<8}  Activity\n  {c}{'─'*54}{r}")

if __name__ == '__main__':
    print_banner()
    cli_log("INFO","Starting Flask server...")
    try:
        app.run(host=HOST,port=PORT,debug=False,use_reloader=False)
    except KeyboardInterrupt:
        print(); cli_log("INFO","Server stopped. Goodbye! 👋"); sys.exit(0)
