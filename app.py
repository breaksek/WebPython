from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import qrcode
import random
import string
from io import BytesIO
from flask import send_file
from datetime import datetime

app = Flask(__name__)

# Fungsi untuk memuat database JSON
def load_data():
    with open('database.json', 'r') as f:
        return json.load(f)

# Fungsi untuk menyimpan data ke dalam database JSON
def save_data(data):
    with open('database.json', 'w') as f:
        json.dump(data, f, indent=4)

# Fungsi untuk menghasilkan ID unik
def generate_unique_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Fungsi untuk memeriksa apakah nama sudah ada di database
def is_name_valid(name):
    data = load_data()
    # Cek apakah nama sudah ada dalam daftar absensi
    return any(entry['name'].lower() == name.lower() for entry in data['absensi'])

# Route untuk halaman absensi manual
@app.route('/')
def index():
    return render_template('index.html')

# Route untuk meng-handle form absensi manual
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    if not name:
        return "Nama tidak boleh kosong", 400

    if not is_name_valid(name):
        return "Nama tidak valid atau belum terdaftar. Silakan coba lagi.", 400

    data = load_data()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['absensi'].append({'name': name, 'timestamp': timestamp})
    save_data(data)
    
    return redirect(url_for('index'))

# Route untuk halaman absensi via QR code
@app.route('/qr')
def qr_absensi():
    return render_template('absensi_form.html')

# Route untuk menerima input dari QR code
@app.route('/qr_submit', methods=['POST'])
def qr_submit():
    name = request.form.get('name')
    if not name:
        return "Nama tidak boleh kosong", 400

    if not is_name_valid(name):
        return "Nama tidak valid atau belum terdaftar. Silakan coba lagi.", 400

    data = load_data()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['absensi'].append({'name': name, 'timestamp': timestamp})
    save_data(data)
    
    return redirect(url_for('qr_absensi'))

# Route untuk menghasilkan QR code dinamis
@app.route('/generate_qr')
def generate_qr():
    unique_id = generate_unique_id()
    qr_url = request.url_root + 'verify/' + unique_id
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')

# Route untuk memverifikasi absensi dari QR code
@app.route('/verify/<unique_id>')
def verify_qr(unique_id):
    data = load_data()
    
    # Cek apakah unique_id ada di dalam database qr_codes
    for entry in data['qr_codes']:
        if entry['id'] == unique_id:
            return redirect(url_for('qr_absensi'))
    
    # Jika ID valid, tambahkan ke database dan redirect ke halaman absensi
    data['qr_codes'].append({'id': unique_id})
    save_data(data)

    # Menyimpan timestamp saat absensi melalui QR code
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['absensi'].append({'name': 'QR Absensi', 'timestamp': timestamp})
    save_data(data)

    return redirect(url_for('qr_absensi'))

if __name__ == '__main__':
    # Buat file database.json jika belum ada
    if not os.path.exists('database.json'):
        with open('database.json', 'w') as f:
            json.dump({'absensi': [], 'qr_codes': []}, f, indent=4)

    app.run(debug=True, host='0.0.0.0')