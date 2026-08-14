# 🏦 Bank Application — Local Build

A locally-hosted banking web application that runs entirely on your computer
with no internet connection required.

---

## 📋 Prerequisites

1. **Python 3.8+** — https://www.python.org/downloads/
2. **MySQL Server** — running locally on your machine
3. The **`bankdb`** database must exist.

### MySQL Setup (one-time)

Open MySQL and run:

```sql
CREATE DATABASE IF NOT EXISTS bankdb;
USE bankdb;
```

---

## 🚀 How to Run

### Windows
Double-click **`run_bank_app.bat`**  
or open a Command Prompt in this folder and type:
```
run_bank_app.bat
```


---

## 🌐 Using the App

1. Run the launcher as above.
2. A CLI window opens and prints the **URL**, **database name**, and **credentials**.
3. Open the printed URL (e.g. `http://127.0.0.1:5000`) in your browser.
4. Use the web interface to open accounts, login, deposit, withdraw, transfer, and more.
5. The CLI window shows live status messages for every banking event.
6. **Press Ctrl+C** in the CLI window to stop the server. The browser page will stop working.

---

## 📁 File Structure

```
bank_app_dist/
├── app.py              ← Flask web server (modified with CLI logging)
├── bank_app.py         ← Core banking logic & database functions
├── run_bank_app.bat    ← Windows launcher
├── run_bank_app.sh     ← Linux/macOS launcher
└── README.md           ← This file
```

---

## ⚙️ DB Credentials (defaults in bank_app.py)

| Setting   | Value          |
|-----------|----------------|
| Host      | localhost       |
| Database  | bankdb         |
| User      | root           |
| Password  | DMistry@126   |

To change these, edit the `DB_CONFIG` dictionary at the top of `bank_app.py`.
