import threading
import time
import requests
import urllib3

# Disable warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetworkManager:
    def __init__(self, url="https://192.168.55.101:5001"):
        self.url = url
        self.state_buffer = None
        self.frame_buffer = None
        self.settings = {"fps": 30, "paused": False}
        self.command_queue = []
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()

    def _loop(self):
        while self.running:
            # Send state if available
            if self.state_buffer:
                try:
                    requests.post(f"{self.url}/api/snake/state", json=self.state_buffer, verify=False)
                    self.connected = True
                except Exception as e:
                    self.connected = False
                    # print(f"Connection error: {e}")
                self.state_buffer = None

            # Send frame if available
            if self.frame_buffer:
                try:
                    requests.post(f"{self.url}/api/stream/snake", data=self.frame_buffer, headers={'Content-Type': 'application/octet-stream'}, verify=False)
                except Exception as e:
                    pass
                self.frame_buffer = None
            
            # Get settings
            try:
                r = requests.get(f"{self.url}/api/snake/settings", verify=False)
                if r.status_code == 200:
                    with self.lock:
                        new_settings = r.json()
                        # Update only if keys exist to avoid overwriting with empty
                        if 'fps' in new_settings:
                            self.settings['fps'] = new_settings['fps']
                        if 'paused' in new_settings:
                            self.settings['paused'] = new_settings['paused']
                    self.connected = True
            except Exception as e:
                self.connected = False

            # Get commands
            try:
                r = requests.get(f"{self.url}/api/snake/commands", verify=False)
                if r.status_code == 200:
                    cmds = r.json()
                    with self.lock:
                        self.command_queue.extend(cmds)
            except:
                pass
            
            time.sleep(0.005) # ~200 updates per second (faster poll)

    def update_state(self, state):
        self.state_buffer = state

    def update_frame(self, frame_bytes):
        self.frame_buffer = frame_bytes

    def get_settings(self):
        with self.lock:
            return self.settings.copy()

    def get_commands(self):
        with self.lock:
            cmds = list(self.command_queue)
            self.command_queue = []
            return cmds

    def stop(self):
        self.running = False
        self.thread.join(timeout=1.0)
