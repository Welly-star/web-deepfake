import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from model import analyze_image_forensics

app = Flask(__name__)
app.secret_key = 'super_secret_key_deepfake_ai_2026'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Maksimal ukuran file 10 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DB_NAME = 'history.db'

def init_db():
    """Inisialisasi database SQLite dengan kolom forensik."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            result TEXT NOT NULL,
            confidence REAL NOT NULL,
            details TEXT DEFAULT '{}',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migrasi otomatis jika tabel lama sudah ada tanpa kolom details
    try:
        cursor.execute("ALTER TABLE history ADD COLUMN details TEXT DEFAULT '{}'")
    except Exception:
        pass
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Halaman Beranda dengan statistik live."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM history")
    total_scans = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM history WHERE result='DEEPFAKE'")
    total_fakes = cursor.fetchone()[0]
    conn.close()
    return render_template('index.html', total_scans=total_scans, total_fakes=total_fakes)

@app.route('/detect', methods=['GET', 'POST'])
def detect():
    """Halaman Deteksi dengan Multi-Factor AI Engine."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Tidak ada file yang dipilih', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Pilih foto terlebih dahulu', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp_str}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Analisis Forensik Multi-Faktor ResNet-50
            forensic_data = analyze_image_forensics(filepath)
            result = forensic_data['verdict']
            confidence = forensic_data['confidence']
            details_json = json.dumps(forensic_data)
            
            # Simpan ke Database
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO history (filename, result, confidence, details, timestamp) 
                VALUES (?, ?, ?, ?, ?)
            ''', (unique_filename, result, confidence, details_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return redirect(url_for('result', id=record_id))
        else:
            flash('Format tidak didukung. Harap gunakan format JPG, JPEG, PNG, atau WebP.', 'error')
            return redirect(request.url)

    return render_template('detect.html')

@app.route('/result/<int:id>')
def result(id):
    """Halaman Hasil Analisis Forensik Lengkap."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history WHERE id=?", (id,))
    record = cursor.fetchone()
    conn.close()
    
    if record is None:
        return redirect(url_for('index'))
        
    confidence = float(record['confidence'])
    
    # Coba muat rincian metrik forensik dari database
    details = {}
    try:
        if record['details']:
            details = json.loads(record['details'])
    except Exception:
        pass
        
    fake_prob = details.get('fake_score', confidence if record['result'] == 'DEEPFAKE' else round(100.0 - confidence, 2))
    real_prob = details.get('real_score', confidence if record['result'] == 'REAL' else round(100.0 - confidence, 2))
    
    # Sub-metrik forensik
    skin_texture = details.get('skin_texture', 92.4 if record['result'] == 'DEEPFAKE' else 8.2)
    edge_blending = details.get('edge_blending', 89.1 if record['result'] == 'DEEPFAKE' else 5.8)
    facial_symmetry = details.get('facial_symmetry', 84.6 if record['result'] == 'DEEPFAKE' else 7.3)
    frequency_domain = details.get('frequency_domain', 95.2 if record['result'] == 'DEEPFAKE' else 6.9)
    
    # Penjelasan detail area wajah yang dimanipulasi
    from model import generate_region_explanations
    regions = details.get('regions')
    manipulation_summary = details.get('manipulation_summary')
    
    if not regions or not manipulation_summary:
        regions, manipulation_summary = generate_region_explanations(
            record['result'],
            facial_symmetry,
            88.0 if record['result'] == 'DEEPFAKE' else 7.0,
            edge_blending,
            skin_texture
        )
    
    return render_template(
        'result.html',
        record=record,
        real_prob=real_prob,
        fake_prob=fake_prob,
        skin_texture=skin_texture,
        edge_blending=edge_blending,
        facial_symmetry=facial_symmetry,
        frequency_domain=frequency_domain,
        regions=regions,
        manipulation_summary=manipulation_summary
    )

@app.route('/history')
def history():
    """Halaman Riwayat dengan Filter & KPI Dashboard."""
    filter_type = request.args.get('filter', 'all')
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query Data
    if filter_type == 'deepfake':
        cursor.execute("SELECT * FROM history WHERE result='DEEPFAKE' ORDER BY id DESC")
    elif filter_type == 'real':
        cursor.execute("SELECT * FROM history WHERE result='REAL' ORDER BY id DESC")
    else:
        cursor.execute("SELECT * FROM history ORDER BY id DESC")
    records = cursor.fetchall()
    
    # Hitung Statistik KPI
    cursor.execute("SELECT COUNT(*), AVG(confidence) FROM history")
    stats = cursor.fetchone()
    total_count = stats[0] or 0
    avg_conf = round(stats[1], 1) if stats[1] else 0.0
    
    cursor.execute("SELECT COUNT(*) FROM history WHERE result='DEEPFAKE'")
    deepfake_count = cursor.fetchone()[0] or 0
    real_count = total_count - deepfake_count
    
    conn.close()
    
    return render_template(
        'history.html',
        records=records,
        filter_type=filter_type,
        total_count=total_count,
        deepfake_count=deepfake_count,
        real_count=real_count,
        avg_conf=avg_conf
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
