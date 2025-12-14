import cv2
import numpy as np
from openni import openni2
from openni import _openni2 as c_api
import mediapipe as mp
import pythoncom 
import pyttsx3
import threading
import queue
import time
import os

# Import Logic
from core.squat_logic import SquatAnalyzer

# --- KONFIGURASI ---
# Point to the new drivers folder
OPENNI_PATH = os.path.join(os.path.dirname(__file__), "drivers")
WEBCAM_INDEX = 1 # Coba 0 jika 1 error
PIXEL_FORMAT_DEPTH_1_MM = 100

class VoiceAssistant:
    def __init__(self):
        self.queue = queue.Queue()
        # Thread jalan terus di background
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        self.last_correction_time = 0

    def _process_queue(self):
        """
        SOLUSI FINAL:
        Kita inisialisasi ulang engine SETIAP KALI mau bicara.
        Ini mencegah engine 'nyangkut' setelah kalimat pertama.
        """
        while True:
            text = self.queue.get()
            if text is None: break # Sinyal stop
            
            try:
                # 1. Wajib Initialize COM untuk setiap loop di thread baru
                pythoncom.CoInitialize()
                
                # 2. Bikin engine BARU setiap kali mau ngomong
                engine = pyttsx3.init()
                engine.setProperty('rate', 160)
                
                # 3. Bicara
                print(f"🔊 Mengucapkan: {text}") # Debug print
                engine.say(text)
                engine.runAndWait()
                
                # 4. Matikan engine secara paksa
                engine.stop()
                del engine
                
            except Exception as e:
                print(f"❌ Error Suara: {e}")
            finally:
                # 5. Bersihkan COM
                pythoncom.CoUninitialize()
                
            self.queue.task_done()

    def say(self, text, is_priority=False):
        current_time = time.time()
        
        # Logika Antrian (Sama seperti sebelumnya)
        if is_priority:
            with self.queue.mutex:
                self.queue.queue.clear()
            self.queue.put(text)
        
        elif (current_time - self.last_correction_time > 3.0): 
            self.queue.put(text)
            self.last_correction_time = current_time

class PostureApp:
    def __init__(self):
        # Init Logic
        self.analyzer = SquatAnalyzer()
        
        # Init Modules dengan Error Handling
        print("[1/3] Menyiapkan Suara...")
        self.voice = VoiceAssistant()
        
        print("[2/3] Menyiapkan Kamera...")
        self.init_camera()
        
        print("[3/3] Menyiapkan AI...")
        self.init_mediapipe()
        
        self.voice.say("Sistem Siap", is_priority=True)

    def init_camera(self):
        # Tambah CAP_DSHOW untuk Windows (Lebih Stabil)
        self.cap = cv2.VideoCapture(WEBCAM_INDEX, cv2.CAP_DSHOW)
        if not self.cap.isOpened(): 
            print("Kamera index 1 gagal, mencoba index 0...")
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
        if not self.cap.isOpened():
            print("❌ FATAL: Kamera RGB tidak ditemukan!")
            exit()
            
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        self.depth_stream = None
        try:
            # Check if initialized to avoid double initialization error
            if not openni2.is_initialized():
                openni2.initialize(OPENNI_PATH)
            
            dev = openni2.Device.open_any()
            self.depth_stream = dev.create_depth_stream()
            self.depth_stream.start()
            self.depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat=PIXEL_FORMAT_DEPTH_1_MM, resolutionX=640, resolutionY=480, fps=30))
            print("✅ Depth Sensor OK")
        except Exception as e:
            print(f"⚠️ Depth Warning (Lanjut tanpa depth): {e}")

    def init_mediapipe(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1)
        self.mp_draw = mp.solutions.drawing_utils

    def run(self):
        print("🚀 Aplikasi Berjalan! (Tekan 'q' di window kamera untuk keluar)")
        while True:
            try:
                ret, frame = self.cap.read()
                if not ret: 
                    print("Gagal membaca frame kamera.")
                    break
                
                # --- DEPTH READING ---
                dist_center = 0
                if self.depth_stream:
                    d_frame = self.depth_stream.read_frame()
                    d_buf = d_frame.get_buffer_as_uint16()
                    img_depth = np.frombuffer(d_buf, dtype=np.uint16).reshape(480, 640)
                    dist_center = img_depth[240, 320]

                # --- AI PROCESSING ---
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_rgb.flags.writeable = False
                results = self.pose.process(img_rgb)
                img_rgb.flags.writeable = True
                frame = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

                if results.pose_landmarks:
                    lm = results.pose_landmarks.landmark
                    
                    # --- LOGIKA UTAMA (Panggil Core) ---
                    analysis = self.analyzer.analyze(lm)
                    
                    # Unpack results
                    knee_angle = analysis["knee_angle"]
                    back_angle = analysis["back_angle"]
                    p_shldr = analysis["p_shldr"]
                    p_hip = analysis["p_hip"]
                    p_knee = analysis["p_knee"]
                    feedback = analysis["feedback"]
                    feedback_color = analysis["feedback_color"]
                    counter = analysis["counter"]
                    voice_command = analysis["voice_command"]
                    standing_hip_y = analysis["standing_hip_y"]
                    is_calibrated = analysis["is_calibrated"]
                    
                    # Handle Voice
                    if voice_command:
                        # Priority for repetition count
                        is_prio = "Repetisi" in voice_command
                        self.voice.say(voice_command, is_priority=is_prio)

                    cx_hip, cy_hip = int(p_hip.x*640), int(p_hip.y*480)
                    
                    # Garis Punggung
                    back_color = (0, 255, 0)
                    if back_angle > 45: back_color = (0, 0, 255) # Hardcoded threshold for visual only
                    cv2.line(frame, (int(p_shldr.x*640), int(p_shldr.y*480)), (cx_hip, cy_hip), back_color, 4)

                    # Visualisasi Calibration Line
                    if is_calibrated:
                        ref_y = int(standing_hip_y * 480)
                        cv2.line(frame, (0, ref_y), (640, ref_y), (0, 255, 0), 1)

                    if 0 < dist_center < 900:
                        cv2.putText(frame, "MUNDUR!", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3)
                        self.voice.say("Harap Mundur", is_priority=False)

                # UI Panel
                cv2.rectangle(frame, (0,0), (320, 120), (0, 0, 0), -1)
                cv2.putText(frame, f'REPS: {self.analyzer.counter}', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
                cv2.putText(frame, self.analyzer.feedback, (10,100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.analyzer.feedback_color, 2)
                
                cv2.imshow('Safe Mode App', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Loop Error: {e}")
                break

        self.cleanup()

    def cleanup(self):
        print("Menutup aplikasi...")
        if self.depth_stream: self.depth_stream.stop()
        openni2.unload()
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = PostureApp()
    app.run()
