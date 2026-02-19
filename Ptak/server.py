import sqlite3
from flask import Flask, request, jsonify, send_from_directory, render_template_string, Response
import os
import time
import io
import threading

app = Flask(__name__, static_url_path='')

# Konfiguracja bazy danych
DB_PATH = 'leaderboard.db'
UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Globalne zmienne dla Snake
snake_state = {
    "score": 0,
    "n_games": 0,
    "snake": [],
    "food": None,
    "timestamp": 0
}

snake_settings = {
    "fps": 30,
    "paused": False
}
snake_commands = []
latest_snake_frame = None
snake_frame_event = threading.Event()

# Globalne zmienne dla Ptak (Live State)
ptak_state = {
    "player_y": 25,
    "pipes": [],
    "score": 0,
    "landmarks": None, # Pose landmarks
    "timestamp": 0,
    "is_playing": False
}
latest_ptak_frame = None
ptak_frame_event = threading.Event()

latest_ptak_camera_frame = None
ptak_camera_frame_event = threading.Event()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  score INTEGER NOT NULL,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  video_path TEXT,
                  image1_path TEXT,
                  image2_path TEXT,
                  image3_path TEXT)''')
    
    # Check if columns exist (for migration)
    c.execute("PRAGMA table_info(scores)")
    columns = [column[1] for column in c.fetchall()]
    if 'video_path' not in columns:
        c.execute("ALTER TABLE scores ADD COLUMN video_path TEXT")
        c.execute("ALTER TABLE scores ADD COLUMN image1_path TEXT")
        c.execute("ALTER TABLE scores ADD COLUMN image2_path TEXT")
        c.execute("ALTER TABLE scores ADD COLUMN image3_path TEXT")
        
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('.', 'ptak.html')

@app.route('/leaderboard')
def board_page():
    return send_from_directory('.', 'ptak_leaderboard.html')

@app.route('/leaderboard1')
def board1_page():
    return send_from_directory('.', 'leaderboard1.html')

@app.route('/leaderboard2')
def board2_page():
    return send_from_directory('.', 'leaderboard2.html')

@app.route('/dashboard')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- API dla Snake ---

@app.route('/api/snake/state', methods=['POST'])
def update_snake_state():
    global snake_state
    data = request.json
    snake_state.update(data)
    snake_state['timestamp'] = time.time()
    return jsonify({'status': 'ok'})

@app.route('/api/snake/state', methods=['GET'])
def get_snake_state():
    return jsonify(snake_state)

@app.route('/api/snake/settings', methods=['POST'])
def update_snake_settings():
    global snake_settings
    data = request.json
    if 'fps' in data:
        snake_settings['fps'] = int(data['fps'])
    if 'paused' in data:
        snake_settings['paused'] = bool(data['paused'])
    return jsonify({'status': 'updated', 'settings': snake_settings})

@app.route('/api/snake/settings', methods=['GET'])
def get_snake_settings():
    return jsonify(snake_settings)

@app.route('/api/snake/command', methods=['POST'])
def add_snake_command():
    global snake_commands
    data = request.json
    if 'command' in data:
        snake_commands.append(data['command'])
    return jsonify({'status': 'added', 'queue_size': len(snake_commands)})

@app.route('/api/snake/commands', methods=['GET'])
def pop_snake_commands():
    global snake_commands
    cmds = list(snake_commands)
    snake_commands = []
    return jsonify(cmds)

# --- API dla Ptaka (Live State) ---

@app.route('/api/ptak/state', methods=['POST'])
def update_ptak_state():
    global ptak_state
    data = request.json
    ptak_state.update(data)
    ptak_state['timestamp'] = time.time()
    return jsonify({'status': 'ok'})

@app.route('/api/ptak/state', methods=['GET'])
def get_ptak_state():
    return jsonify(ptak_state)

# --- API dla Streaming (Screen Mirror) ---

@app.route('/api/stream/snake', methods=['POST'])
def update_snake_frame():
    global latest_snake_frame
    if request.data:
        latest_snake_frame = request.data
        snake_frame_event.set()
        return "OK", 200
    return "No data", 400

def gen_snake_frames():
    while True:
        if snake_frame_event.wait(timeout=1.0): # Wait for new frame
            snake_frame_event.clear()
            if latest_snake_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_snake_frame + b'\r\n')
        else:
            # Send keepalive or last frame if timeout
            if latest_snake_frame:
                 yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_snake_frame + b'\r\n')

@app.route('/api/stream/snake/mjpeg')
def stream_snake_mjpeg():
    return Response(gen_snake_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/stream/ptak', methods=['POST'])
def update_ptak_frame():
    global latest_ptak_frame
    if request.data:
        latest_ptak_frame = request.data
        ptak_frame_event.set()
        return "OK", 200
    return "No data", 400

def gen_ptak_frames():
    while True:
        if ptak_frame_event.wait(timeout=1.0):
            ptak_frame_event.clear()
            if latest_ptak_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_ptak_frame + b'\r\n')
        else:
             if latest_ptak_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_ptak_frame + b'\r\n')

@app.route('/api/stream/ptak/mjpeg')
def stream_ptak_mjpeg():
    return Response(gen_ptak_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/stream/ptak/camera', methods=['POST'])
def update_ptak_camera_frame():
    global latest_ptak_camera_frame
    if request.data:
        latest_ptak_camera_frame = request.data
        ptak_camera_frame_event.set()
        return "OK", 200
    return "No data", 400

def gen_ptak_camera_frames():
    while True:
        if ptak_camera_frame_event.wait(timeout=1.0):
            ptak_camera_frame_event.clear()
            if latest_ptak_camera_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_ptak_camera_frame + b'\r\n')
        else:
            if latest_ptak_camera_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_ptak_camera_frame + b'\r\n')

@app.route('/api/stream/ptak/camera/mjpeg')
def stream_ptak_camera_mjpeg():
    return Response(gen_ptak_camera_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# --- API dla Mediów Ptaka ---

@app.route('/api/media', methods=['GET'])
def list_media():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)), reverse=True)
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/media/<filename>', methods=['DELETE'])
def delete_media(filename):
    try:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(path):
            os.remove(path)
            return jsonify({'status': 'deleted'})
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Istniejące API Ptaka ---

@app.route('/api/scores', methods=['GET'])
def get_scores():
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT name, score, id FROM scores ORDER BY score DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        
        # Formatowanie danych do JSON
        data = [{'name': row[0], 'score': row[1], 'id': row[2]} for row in rows]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest_game', methods=['GET'])
def get_latest_game():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Get the most recently inserted game (by ID descending)
        c.execute('SELECT name, score, video_path, image1_path, image2_path, image3_path, id FROM scores ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        
        if row:
            data = {
                'name': row[0],
                'score': row[1],
                'video': row[2],
                'images': [row[3], row[4], row[5]],
                'id': row[6]
            }
            return jsonify(data)
        else:
            return jsonify(None)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scores', methods=['POST'])
def add_score():
    try:
        data = request.json
        name = data.get('name', 'ANON')
        score = data.get('score', 0)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO scores (name, score) VALUES (?, ?)', (name, score))
        score_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'id': score_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_media/<int:score_id>', methods=['POST'])
def upload_media(score_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        video = request.files.get('video')
        images = request.files.getlist('images') # Expecting list of images
        
        video_path = None
        image_paths = [None, None, None]
        
        if video:
            filename = f"game_{score_id}.webm"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            video.save(filepath)
            video_path = f"/uploads/{filename}"
            c.execute("UPDATE scores SET video_path = ? WHERE id = ?", (video_path, score_id))
            
        for i, img in enumerate(images):
            if i >= 3: break
            filename = f"game_{score_id}_img_{i}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            img.save(filepath)
            image_paths[i] = f"/uploads/{filename}"
            
            # Update specific column
            col_name = f"image{i+1}_path"
            c.execute(f"UPDATE scores SET {col_name} = ? WHERE id = ?", (image_paths[i], score_id))
            
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Upewnij się, że jesteśmy w katalogu skryptu
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    init_db()
    print("===============================================================")
    print(" SERWER GRY URUCHOMIONY (HTTPS)")
    print(" Gra dostepna pod adresem: https://localhost:5001")
    print(" Leaderboard dostepny pod adresem: https://localhost:5001/leaderboard")
    print(" Dashboard dostepny pod adresem: https://localhost:5001/dashboard")
    print("===============================================================")
    # Uzywamy ssl_context='adhoc' dla HTTPS (wymaga pyopenssl)
    app.run(host='0.0.0.0', port=5001, threaded=True, ssl_context='adhoc')
