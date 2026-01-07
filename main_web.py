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
st.set_page_config(
    page_title="Squat AI Pro", 
    layout="wide",
    page_icon="🏋️",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        /* Main theme colors */
        :root {
            --primary-color: #0068C9;
            --secondary-color: #4FC3F7;
            --success-color: #00C853;
            --warning-color: #FF9800;
            --danger-color: #F44336;
            --dark-bg: #0E1117;
            --card-bg: #262730;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%);
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .main-header h1 {
            color: white;
            font-size: 3rem;
            font-weight: bold;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .main-header p {
            color: #E0E0E0;
            font-size: 1.2rem;
            margin-top: 0.5rem;
        }
        
        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            margin-bottom: 1rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        .metric-title {
            color: #E0E0E0;
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: white;
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0;
        }
        
        /* Feedback card */
        .feedback-card {
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .feedback-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .feedback-warning {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .feedback-error {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }
        
        .feedback-text {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }
        
        /* Video frame */
        .video-container {
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
            background: #000;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #0068C9 0%, #4FC3F7 100%);
        }
        
        /* Stats section */
        .stats-header {
            background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        .stats-header h3 {
            color: white;
            margin: 0;
            font-size: 1.5rem;
        }
        
        /* Pulse animation for active status */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(102, 126, 234, 0); }
            100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        /* Button styling */
        .stCheckbox {
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        /* Info boxes */
        .info-box {
            background: rgba(255, 255, 255, 0.05);
            border-left: 4px solid #0068C9;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%); border-radius: 10px; margin-bottom: 1rem;'>
        <h2 style='color: white; margin: 0;'>⚙️ Pengaturan</h2>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
    <div class='info-box'>
        <strong>🖥️ Sistem Operasi:</strong><br>
        <span style='color: #4FC3F7; font-weight: bold;'>{OS_NAME}</span>
    </div>
""", unsafe_allow_html=True)

# Pilihan Kamera
st.sidebar.markdown("### 📹 Konfigurasi Kamera")
cam_index = st.sidebar.selectbox("Pilih Index Kamera", [0, 1, 2], index=0)

# Toggle Depth (Otomatis dimatikan/disabled jika bukan Windows)
st.sidebar.markdown("### 🎯 Sensor Kedalaman")
use_depth = st.sidebar.toggle("Gunakan Depth Sensor", value=IS_WINDOWS, disabled=not IS_WINDOWS)
if not IS_WINDOWS:
    st.sidebar.warning("⚠️ Fitur Depth dimatikan karena Anda menggunakan Mac/Linux. Mode RGB Only.")
else:
    st.sidebar.success("✅ Depth sensor tersedia")

# Informasi tambahan
st.sidebar.markdown("---")
st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 10px;'>
        <h4 style='color: #4FC3F7; margin-bottom: 0.5rem;'>📖 Panduan Cepat</h4>
        <p style='font-size: 0.9rem; line-height: 1.6;'>
            1. Pilih kamera yang sesuai<br>
            2. Klik tombol MULAI ANALISIS<br>
            3. Posisikan tubuh di depan kamera<br>
            4. Lakukan squat dengan benar
        </p>
    </div>
""", unsafe_allow_html=True)# --- FUNGSI UTAMA ---
def home_page():
    st.markdown("""
        <div class='main-header'>
            <h1>🏋️ Smart Biomechanical Squat Assistant</h1>
            <p>Selamat datang di aplikasi analisis gerakan squat berbasis AI</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
            <h2 style='color: #4FC3F7; text-align: center;'>📋 Apa itu Smart Biomechanical Squat Assistant?</h2>
            <p style='font-size: 1.1rem; line-height: 1.6; color: white;'>
                Aplikasi ini adalah alat canggih yang menggunakan kecerdasan buatan (AI) untuk menganalisis gerakan squat Anda secara real-time. 
                Dengan bantuan kamera dan algoritma computer vision, aplikasi ini dapat mendeteksi postur tubuh, menghitung repetisi, 
                dan memberikan feedback langsung untuk membantu Anda melakukan squat dengan teknik yang benar.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style='background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;'>
                <h3 style='color: #FFD700;'>🎯 Fitur Utama</h3>
                <ul style='color: white; font-size: 1rem; line-height: 1.8;'>
                    <li>Analisis real-time gerakan squat</li>
                    <li>Deteksi sudut lutut dan punggung</li>
                    <li>Penghitungan repetisi otomatis</li>
                    <li>Feedback visual dan teks</li>
                    <li>Visualisasi pose dengan MediaPipe</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;'>
                <h3 style='color: #FFD700;'>💡 Manfaat</h3>
                <ul style='color: white; font-size: 1rem; line-height: 1.8;'>
                    <li>Mencegah cedera saat berolahraga</li>
                    <li>Meningkatkan teknik squat yang benar</li>
                    <li>Pelatihan tanpa instruktur</li>
                    <li>Monitoring progress latihan</li>
                    <li>Cocok untuk pemula dan mahir</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%); border-radius: 15px;'>
            <h3 style='color: white; margin-bottom: 1rem;'>🚀 Siap Memulai?</h3>
            <p style='color: #E0E0E0; font-size: 1.1rem;'>Pilih menu "Analisis Squat" di sidebar untuk mulai menggunakan aplikasi</p>
        </div>
    """, unsafe_allow_html=True)

def credit_page():
    st.markdown("""
        <div class='main-header'>
            <h1>👥 Credits</h1>
            <p>Tim pengembang di balik Smart Biomechanical Squat Assistant</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;'>
            <h2 style='color: #4FC3F7;'>Terima Kasih Kepada Tim Pengembang</h2>
            <p style='font-size: 1.1rem; color: white;'>Aplikasi ini dibuat oleh mahasiswa PCD (Pengolahan Citra Digital) sebagai bagian dari tugas akhir semester.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                <h3 style='color: white; margin-bottom: 0.5rem;'>Adrian Pratama Sasmita</h3>
                <p style='color: #E0E0E0; font-size: 1rem;'>NIM: 231524043</p>
                <p style='color: #FFD700; font-size: 0.9rem;'>👨‍💻 Developer</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                <h3 style='color: white; margin-bottom: 0.5rem;'>Fanza Atsila Fizarli</h3>
                <p style='color: #E0E0E0; font-size: 1rem;'>NIM: 231524043</p>
                <p style='color: #FFD700; font-size: 0.9rem;'>🎨 UI/UX Designer</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                <h3 style='color: white; margin-bottom: 0.5rem;'>Luthfi Satrio Wicaksono</h3>
                <p style='color: #E0E0E0; font-size: 1rem;'>NIM: 231524049</p>
                <p style='color: #FFD700; font-size: 0.9rem;'>🔧 System Architect</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 15px; text-align: center;'>
            <h3 style='color: #4FC3F7;'>📚 Teknologi yang Digunakan</h3>
            <div style='display: flex; justify-content: center; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;'>
                <span style='background: #0068C9; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;'>Streamlit</span>
                <span style='background: #0068C9; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;'>OpenCV</span>
                <span style='background: #0068C9; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;'>MediaPipe</span>
                <span style='background: #0068C9; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;'>NumPy</span>
                <span style='background: #0068C9; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;'>Python</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def analysis_page():
    # Header
    st.markdown("""
        <div class='main-header'>
            <h1>🏋️ Analisis Squat Real-Time</h1>
            <p>Analisis gerakan squat Anda secara real-time dengan AI</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_video, col_stats = st.columns([2.5, 1])
    
    with col_stats:
        st.markdown("""
            <div class='stats-header'>
                <h3>📊 Statistik Live</h3>
            </div>
        """, unsafe_allow_html=True)
        
        ph_reps = st.empty()
        ph_angle = st.empty()
        ph_back_angle = st.empty()
        ph_feedback = st.empty()
        ph_tips = st.empty()

    with col_video:
        st.markdown("<div class='video-container'>", unsafe_allow_html=True)
        ph_frame = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)

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
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        run = st.checkbox('🔴 MULAI ANALISIS', value=True, key='start_button')
    
    if not run:
        st.info("👆 Klik tombol di atas untuk memulai analisis squat")
        return
    
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
        back_angle = 0
        
        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            
            # Panggil Logic
            data = analyzer.analyze(lm)
            
            current_reps = data["counter"]
            current_feedback = data["feedback"]
            knee_angle = data["knee_angle"]
            back_angle = data["back_angle"]
            
            # Visualisasi
            mp_draw.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=(255, 255, 0), thickness=2, circle_radius=2)
            )
            
            # Garis Punggung dengan gradient effect
            p_shldr = data["p_shldr"]
            p_hip = data["p_hip"]
            start_pt = (int(p_shldr.x * frame.shape[1]), int(p_shldr.y * frame.shape[0]))
            end_pt = (int(p_hip.x * frame.shape[1]), int(p_hip.y * frame.shape[0]))
            
            line_color = (0, 255, 0) if back_angle < 45 else (0, 165, 255)
            cv2.line(frame, start_pt, end_pt, line_color, 5)
            
            # Tambahkan info overlay pada video
            overlay_y = 40
            cv2.rectangle(frame, (10, 10), (300, 130), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (300, 130), (102, 126, 234), 2)
            
            cv2.putText(frame, f"Reps: {current_reps}", (20, overlay_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            overlay_y += 30
            cv2.putText(frame, f"Knee: {int(knee_angle)} deg", (20, overlay_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            overlay_y += 25
            cv2.putText(frame, f"Back: {int(back_angle)} deg", (20, overlay_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            overlay_y += 25
            
            # Status indicator
            status_color_bgr = (0, 255, 0) if "BAGUS" in current_feedback else (0, 0, 255) if "JANGAN" in current_feedback else (0, 165, 255)
            cv2.circle(frame, (280, 30), 10, status_color_bgr, -1)

        # 3. Update UI
        # Tentukan feedback class
        feedback_class = "feedback-success"
        if "JANGAN" in current_feedback or "TURUNKAN" in current_feedback:
            feedback_class = "feedback-error"
        elif "NAIK" in current_feedback or "Menunggu" in current_feedback:
            feedback_class = "feedback-warning"
        
        # Update metrics dengan styling
        ph_reps.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>🔢 Repetisi</div>
                <div class='metric-value'>{current_reps}</div>
            </div>
        """, unsafe_allow_html=True)
        
        ph_angle.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>🦵 Sudut Lutut</div>
                <div class='metric-value'>{int(knee_angle)}°</div>
            </div>
        """, unsafe_allow_html=True)
        
        ph_back_angle.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>📐 Sudut Punggung</div>
                <div class='metric-value'>{int(back_angle)}°</div>
            </div>
        """, unsafe_allow_html=True)
        
        ph_feedback.markdown(f"""
            <div class='feedback-card {feedback_class} pulse'>
                <div class='feedback-text'>{current_feedback}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tips berdasarkan feedback
        tips_text = ""
        if "BAGUS" in current_feedback:
            tips_text = "✅ Pertahankan postur yang bagus!"
        elif "JANGAN" in current_feedback:
            tips_text = "⚠️ Jaga agar lutut tidak melewati jari kaki"
        elif "TURUNKAN" in current_feedback:
            tips_text = "📏 Turunkan tubuh lebih dalam (minimal 90°)"
        else:
            tips_text = "👀 Posisikan tubuh Anda di depan kamera"
            
        ph_tips.info(tips_text)

        # 4. Tampilkan Frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ph_frame.image(frame, channels="RGB", use_container_width=True)

    # Cleanup
    cap.release()
    if depth_stream: 
        depth_stream.stop()
        openni2.unload()
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #0068C9 0%, #4FC3F7 100%); border-radius: 15px;'>
            <h3 style='color: white; margin-bottom: 1rem;'>💡 Tips untuk Squat yang Sempurna</h3>
            <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1rem;'>
                <div style='flex: 1; min-width: 200px; background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;'>
                    <h4 style='color: #FFD700;'>🦵 Lutut</h4>
                    <p style='color: white; font-size: 0.9rem;'>Jangan biarkan lutut melewati jari kaki</p>
                </div>
                <div style='flex: 1; min-width: 200px; background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;'>
                    <h4 style='color: #FFD700;'>📐 Kedalaman</h4>
                    <p style='color: white; font-size: 0.9rem;'>Turunkan hingga paha sejajar lantai (90°)</p>
                </div>
                <div style='flex: 1; min-width: 200px; background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;'>
                    <h4 style='color: #FFD700;'>🧍 Postur</h4>
                    <p style='color: white; font-size: 0.9rem;'>Jaga punggung tetap lurus</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def main():
    # Navigation buttons above sidebar
    st.markdown("""
        <div style='display: flex; justify-content: center; gap: 1rem; margin-bottom: 2rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 15px;'>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Beranda", use_container_width=True):
            st.session_state.page = "home"
    
    with col2:
        if st.button("🏋️ Analisis Squat", use_container_width=True):
            st.session_state.page = "analysis"
    
    with col3:
        if st.button("👥 Credits", use_container_width=True):
            st.session_state.page = "credits"
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Initialize page state
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    # Display selected page
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "analysis":
        analysis_page()
    elif st.session_state.page == "credits":
        credit_page()

if __name__ == "__main__":
    main()