import sqlite3
from flask import Flask, request, jsonify, send_from_directory, render_template_string, Response
import os
import time
import io
import threading
import subprocess
import shutil
import uuid

app = Flask(__name__, static_folder=None)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max per frame (720p JPEG)

# Konfiguracja bazy danych
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'leaderboard.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
JS_FOLDER = os.path.join(BASE_DIR, 'js')
CSS_FOLDER = os.path.join(BASE_DIR, 'css')

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

# -----------------------------------------------------------------------
# SSL CERTIFICATE (persistent self-signed - browser remembers it)
# -----------------------------------------------------------------------
SSL_CERT = os.path.join(BASE_DIR, 'ssl_cert.pem')
SSL_KEY  = os.path.join(BASE_DIR, 'ssl_key.pem')

def ensure_ssl_cert():
    """Generate a persistent self-signed certificate if it doesn't exist.
    Using a stable cert means the browser only asks for trust once."""
    if os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY):
        return (SSL_CERT, SSL_KEY)
    print("[SSL] Generating persistent self-signed certificate...")
    try:
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', SSL_KEY,
            '-out',    SSL_CERT,
            '-days',   '3650',
            '-nodes',
            '-subj',   '/CN=targi-server/O=Targi/C=PL',
            '-addext', 'subjectAltName=IP:192.168.55.101,IP:127.0.0.1,DNS:localhost'
        ], check=True, capture_output=True)
        print(f"[SSL] Certificate saved to {SSL_CERT}")
        return (SSL_CERT, SSL_KEY)
    except Exception as e:
        print(f"[SSL] openssl failed: {e} – falling back to adhoc cert")
        return 'adhoc'

# -----------------------------------------------------------------------
# HARDWARE ACCELERATION DETECTION (VAAPI on Debian/Intel/AMD)
# -----------------------------------------------------------------------
def detect_ffmpeg_encoder():
    """Prefer VAAPI (Intel/AMD GPU on Debian), fallback to libx264."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True, text=True, timeout=5
        )
        encoders = result.stdout + result.stderr

        # Check for VAAPI device
        vaapi_device = '/dev/dri/renderD128'
        has_vaapi_dev = os.path.exists(vaapi_device)
        has_vaapi_enc = 'h264_vaapi' in encoders

        if has_vaapi_dev and has_vaapi_enc:
            print(f"[FFmpeg] Using VAAPI hardware encoder ({vaapi_device})")
            return 'vaapi'

        # NVENC (NVIDIA)
        if 'h264_nvenc' in encoders:
            print("[FFmpeg] Using NVENC hardware encoder")
            return 'nvenc'

        print("[FFmpeg] Using software libx264 encoder (no GPU acceleration found)")
        return 'software'
    except Exception as e:
        print(f"[FFmpeg] Detection failed: {e} – using software encoder")
        return 'software'

FFMPEG_ENCODER = detect_ffmpeg_encoder()

# --- STREAM RECORDER ---
class StreamRecorder:
    def __init__(self):
        self.proc = None
        self.lock = threading.Lock()
        self.current_file = None

    def _build_cmd(self, filepath):
        """Build FFmpeg command optimized for the detected encoder.
        Input: MJPEG frames at 60fps via stdin.
        Output: H.264 MP4 compatible with Windows 10 Chrome/Edge/VLC."""

        base = [
            'ffmpeg', '-y',
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-r', '60',          # 60fps input (matches camera stream rate)
            '-i', '-',
        ]

        if FFMPEG_ENCODER == 'vaapi':
            # VAAPI: GPU-accelerated encoding on Intel/AMD (Debian)
            # Upload frames to GPU, encode H.264, download result
            encode = [
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2,format=nv12,hwupload',
                '-c:v', 'h264_vaapi',
                '-vaapi_device', '/dev/dri/renderD128',
                '-qp', '22',             # Quality: 0=lossless, 51=worst (22 ≈ high quality)
                '-profile:v', 'main',    # H.264 Main Profile – Windows 10 compatible
            ]
        elif FFMPEG_ENCODER == 'nvenc':
            encode = [
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                '-c:v', 'h264_nvenc',
                '-preset', 'p4',
                '-cq', '22',
                '-profile:v', 'main',
            ]
        else:
            # Software libx264 – universally compatible
            encode = [
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Min CPU load on server
                '-crf', '20',            # Good quality
                '-profile:v', 'baseline', # Max Win10 browser compat
                '-level', '4.0',
            ]

        output = [
            '-pix_fmt', 'yuv420p',       # Required for all players
            '-movflags', '+faststart',   # MP4 header at front – instant stream/play on Win10
            filepath
        ]

        return base + encode + output

    def start(self, filename):
        with self.lock:
            if self.proc:
                self.stop()
            
            self.current_file = filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            cmd = self._build_cmd(filepath)
            
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    # Increase pipe buffer on Linux for smoother 60fps ingest
                    bufsize=4 * 1024 * 1024  # 4 MB pipe buffer
                )
                print(f"[Recorder] Started: {filepath} (encoder: {FFMPEG_ENCODER})")
            except FileNotFoundError:
                print("[Recorder] ERROR: ffmpeg not found! Install with: sudo apt install ffmpeg")
            except Exception as e:
                print(f"[Recorder] Failed to start: {e}")

    def write(self, frame_data):
        if self.proc and self.proc.stdin:
            try:
                self.proc.stdin.write(frame_data)
                self.proc.stdin.flush()
            except BrokenPipeError:
                print("[Recorder] Pipe broken, stopping recorder.")
                self.stop()
            except Exception:
                pass

    def stop(self):
        with self.lock:
            if self.proc:
                try:
                    if self.proc.stdin:
                        self.proc.stdin.close()
                    self.proc.wait(timeout=5)  # Wait up to 5s for FFmpeg to finalize
                except subprocess.TimeoutExpired:
                    print("[Recorder] FFmpeg timeout – killing process")
                    self.proc.kill()
                    self.proc.wait()
                except Exception as e:
                    print(f"[Recorder] Stop error: {e}")
                    if self.proc:
                        self.proc.kill()
                
                self.proc = None
                print(f"[Recorder] Stopped, file saved: {self.current_file}")
                return self.current_file
            return None

recorder = StreamRecorder()

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
    return send_from_directory(BASE_DIR, 'ptak.html')

@app.route('/leaderboard')
def board_page():
    return send_from_directory(BASE_DIR, 'ptak_leaderboard.html')

@app.route('/leaderboard1')
def board1_page():
    return send_from_directory(BASE_DIR, 'leaderboard1.html')

@app.route('/leaderboard2')
def board2_page():
    return send_from_directory(BASE_DIR, 'leaderboard2.html')

@app.route('/dashboard')
def dashboard_page():
    return send_from_directory(BASE_DIR, 'dashboard.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    response = send_from_directory(UPLOAD_FOLDER, filename)
    # Allow Windows 10 leaderboard to load videos cross-origin
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(JS_FOLDER, filename)

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(CSS_FOLDER, filename)

@app.route('/favicon.ico')
def favicon():
    return '', 204

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
        if snake_frame_event.wait(timeout=1.0):
            snake_frame_event.clear()
            if latest_snake_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_snake_frame + b'\r\n')
        else:
            if latest_snake_frame:
                 yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_snake_frame + b'\r\n')

@app.route('/api/stream/snake/mjpeg')
def stream_snake_mjpeg():
    response = Response(gen_snake_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    _apply_stream_headers(response)
    return response


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
    response = Response(gen_ptak_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    _apply_stream_headers(response)
    return response


@app.route('/api/stream/ptak/camera', methods=['POST'])
def update_ptak_camera_frame():
    global latest_ptak_camera_frame
    if request.data:
        latest_ptak_camera_frame = request.data
        
        # Write to recorder if active
        recorder.write(request.data)
        
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
    response = Response(gen_ptak_camera_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    _apply_stream_headers(response)
    return response

def _apply_stream_headers(response):
    """Headers that ensure smooth MJPEG delivery to Chromium (Debian) and Chrome/Edge (Win10)."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering if behind proxy
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# --- API dla Nagrywania (New) ---

@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    # Use unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())
    filename = f"rec_{int(time.time())}_{unique_id[:8]}.mp4"
    recorder.start(filename)
    return jsonify({'status': 'started', 'filename': filename})

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    filename = recorder.stop()
    return jsonify({'status': 'stopped', 'filename': filename})


# --- API dla Mediów Ptaka ---

@app.route('/api/media', methods=['GET'])
def list_media():
    try:
        # Get all scores with video paths
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Join not needed as we just want to list files that have metadata
        c.execute('SELECT id, name, score, video_path, date FROM scores WHERE video_path IS NOT NULL ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        
        media_list = []
        for row in rows:
            # row: (id, name, score, video_path, date)
            video_path = row[3]
            if not video_path: continue
            
            filename = os.path.basename(video_path)
            
            # Check if file actually exists
            if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                media_list.append({
                    'id': row[0],
                    'name': row[1],
                    'score': row[2],
                    'filename': filename,
                    'date': row[4],
                    'type': 'video' if filename.endswith(('.mp4', '.webm')) else 'image'
                })
        
        return jsonify(media_list)
    except Exception as e:
        print(f"Error listing media: {e}")
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
        # Zmieniono zapytanie, aby filtrowac wyniki <= 0
        c.execute('SELECT name, score, id, video_path FROM scores WHERE score > 0 ORDER BY score DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        
        # Formatowanie danych do JSON
        data = [{'name': row[0], 'score': row[1], 'id': row[2], 'video_path': row[3]} for row in rows]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Get latest games
        c.execute('SELECT name, score, id, video_path, date FROM scores ORDER BY date DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        conn.close()
        
        data = [{
            'name': row[0], 
            'score': row[1], 
            'id': row[2], 
            'video_path': row[3],
            'date': row[4]
        } for row in rows]
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
        
        # Check if we should link the temporary recording
        link_recording = data.get('link_recording', False)
        recording_filename = data.get('recording_filename', None)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO scores (name, score) VALUES (?, ?)', (name, score))
        score_id = c.lastrowid
        
        # Handle recording linking
        if link_recording and recording_filename:
            temp_path = os.path.join(UPLOAD_FOLDER, recording_filename)
            new_filename = f"game_{score_id}.mp4"
            new_path = os.path.join(UPLOAD_FOLDER, new_filename)
            
            if os.path.exists(temp_path):
                try:
                    # Use shutil.move for cross-fs safety
                    shutil.move(temp_path, new_path)
                    
                    video_url = f"/uploads/{new_filename}"
                    c.execute("UPDATE scores SET video_path = ? WHERE id = ?", (video_url, score_id))
                except Exception as e:
                    print(f"Error renaming recording: {e}")
            else:
                 print(f"Recording file not found: {temp_path}")
        
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
        # images = request.files.getlist('images') # Removed
        
        video_path = None
        # image_paths = [None, None, None]
        
        if video:
            filename = f"game_{score_id}.webm"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            video.save(filepath)
            video_path = f"/uploads/{filename}"
            c.execute("UPDATE scores SET video_path = ? WHERE id = ?", (video_path, score_id))
            
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Upewnij się, że jesteśmy w katalogu skryptu
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    init_db()
    ssl_ctx = ensure_ssl_cert()
    
    print("===============================================================")
    print(" SERWER GRY URUCHOMIONY (HTTPS)")
    print(" Gra:         https://192.168.55.101:5001")
    print(" Leaderboard: https://192.168.55.101:5001/leaderboard")
    print(" Dashboard:   https://192.168.55.101:5001/dashboard")
    print(f" FFmpeg encoder: {FFMPEG_ENCODER}")
    print("===============================================================")
    app.run(host='0.0.0.0', port=5001, threaded=True, ssl_context=ssl_ctx)
