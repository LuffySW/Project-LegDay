import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
import os
import platform # Library untuk cek OS
from core.squat_logic import SquatAnalyzer

# --- DETEKSI SISTEM OPERASI ---
OS_NAME = platform.system() # "Windows" atau "Darwin" (Mac)
IS_WINDOWS = OS_NAME == "Windows"

# --- IMPORT DRIVER (HANYA JIKA WINDOWS) ---
openni2 = None
if IS_WINDOWS:
    try:
        from openni import openni2
        # Setup path driver khusus Windows
        OPENNI_PATH = os.path.join(os.path.dirname(__file__), "drivers")
    except ImportError:
        pass

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Squat AI Pro", layout="wide")

st.markdown("""
    <style>
        .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Pengaturan")
st.sidebar.info(f"Detected OS: {OS_NAME}")

# Pilihan Kamera
# Mac user biasanya kamera default index 0 atau 1
cam_index = st.sidebar.selectbox("Pilih Index Kamera", [0, 1, 2], index=0)

# Toggle Depth (Otomatis dimatikan/disabled jika bukan Windows)
use_depth = st.sidebar.toggle("Gunakan Depth Sensor", value=IS_WINDOWS, disabled=not IS_WINDOWS)
if not IS_WINDOWS:
    st.sidebar.caption("⚠️ Fitur Depth dimatikan karena Anda menggunakan Mac/Linux. Mode RGB Only.")

# --- FUNGSI UTAMA ---
def main():
    st.title("🏋️ Smart Biomechanical Squat Assistant")
    
    col_video, col_stats = st.columns([3, 1])
    
    with col_stats:
        st.markdown("### 📊 Live Stats")
        ph_reps = st.empty()
        ph_feedback = st.empty()
        ph_angle = st.empty()

    with col_video:
        ph_frame = st.empty()

    # --- INIT AI ---
    analyzer = SquatAnalyzer()
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1)
    mp_draw = mp.solutions.drawing_utils

    # --- INIT KAMERA (CROSS PLATFORM) ---
    # Jika Windows pakai CAP_DSHOW agar cepat, Jika Mac pakai default (AVFoundation)
    if IS_WINDOWS:
        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(cam_index) # Mac Default
    
    # --- INIT DEPTH (WINDOWS ONLY) ---
    depth_stream = None
    if use_depth and IS_WINDOWS and openni2:
        try:
            if not openni2.is_initialized():
                openni2.initialize(OPENNI_PATH)
            dev = openni2.Device.open_any()
            depth_stream = dev.create_depth_stream()
            depth_stream.start()
        except Exception as e:
            st.sidebar.error(f"Depth Error: {e}")

    # Tombol Mulai
    run = st.checkbox('🔴 MULAI ANALISIS', value=True)
    
    while run:
        ret, frame = cap.read()
        if not ret:
            st.warning(f"Kamera index {cam_index} tidak terdeteksi.")
            break

        # 1. AI Process
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)
        
        # 2. Logic Core
        current_feedback = "Menunggu..."
        current_reps = 0
        knee_angle = 0
        
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            
            # Panggil Logic
            data = analyzer.analyze(lm)
            
            current_reps = data["counter"]
            current_feedback = data["feedback"]
            knee_angle = data["knee_angle"]
            back_angle = data["back_angle"]
            
            # Visualisasi
            mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # Garis Punggung
            p_shldr = data["p_shldr"]
            p_hip = data["p_hip"]
            start_pt = (int(p_shldr.x * frame.shape[1]), int(p_shldr.y * frame.shape[0]))
            end_pt = (int(p_hip.x * frame.shape[1]), int(p_hip.y * frame.shape[0]))
            
            line_color = (0, 255, 0) if back_angle < 45 else (0, 0, 255)
            cv2.line(frame, start_pt, end_pt, line_color, 4)

        # 3. Update UI
        status_color = "green" if current_feedback == "BAGUS!" else "red" if "JANGAN" in current_feedback or "TURUNKAN" in current_feedback else "orange"
        
        ph_reps.metric("Repetisi", f"{current_reps}")
        ph_angle.metric("Sudut Lutut", f"{int(knee_angle)}°")
        ph_feedback.markdown(f"### Status:\n:{status_color}[**{current_feedback}**]")

        # 4. Tampilkan Frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ph_frame.image(frame, channels="RGB", use_container_width=True)

    # Cleanup
    cap.release()
    if depth_stream: 
        depth_stream.stop()
        openni2.unload()

if __name__ == "__main__":
    main()