from flask import Flask, render_template, request
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)

# --- SETTING TELEGRAM ---
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

# --- INISIALISASI DATABASE ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            city TEXT,
            country TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def send_telegram_message(message):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        payload = {'chat_id': CHAT_ID, 'text': message}
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

@app.route('/')
def index():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Cek lokasi dari API publik
    try:
        res = requests.get(f'https://ipapi.co/{ip}/json/').json()
        city = res.get('city', 'Unknown')
        country = res.get('country_name', 'Unknown')
    except:
        city = country = 'Unknown'

    # Simpan data kunjungan ke DB
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO visitors (ip, city, country) VALUES (?, ?, ?)", (ip, city, country))
    conn.commit()

    # Hitung total kunjungan dari IP yang sama
    c.execute("SELECT COUNT(*) FROM visitors WHERE ip = ?", (ip,))
    total_visits = c.fetchone()[0]
    conn.close()

    # Kirim notifikasi ke Telegram
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    message = f"🌐 IP Baru Masuk:\nIP: {ip}\nKota: {city}\nNegara: {country}\nTotal Kunjungan: {total_visits}\nWaktu: {now}"
    send_telegram_message(message)

    return render_template('index.html', ip=ip, city=city, country=country, visits=total_visits)
