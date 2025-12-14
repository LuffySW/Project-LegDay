import numpy as np

# Tuning Constants
SMOOTHING_FACTOR = 0.5
HIP_DROP_THRESHOLD = 0.08
BACK_FAIL_THRESHOLD = 45

class SquatAnalyzer:
    def __init__(self):
        self.counter = 0
        self.stage = "UP"
        self.feedback = "SIAP"
        self.feedback_color = (255, 255, 0)
        
        self.prev_knee_angle = 180
        self.prev_back_angle = 0
        self.standing_hip_y = 0
        self.is_calibrated = False

    def calculate_angle(self, a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        if angle > 180.0: angle = 360-angle
        return angle

    def smooth_value(self, current, prev):
        return (SMOOTHING_FACTOR * prev) + ((1 - SMOOTHING_FACTOR) * current)

    def analyze(self, landmarks):
        # Determine side
        vis_left = landmarks[23].visibility
        vis_right = landmarks[24].visibility
        side = "LEFT" if vis_left > vis_right else "RIGHT"

        if side == "LEFT": idx = [11, 23, 25, 27] 
        else: idx = [12, 24, 26, 28]

        p_shldr, p_hip, p_knee, p_ankle = [landmarks[i] for i in idx]

        # Calculate angles
        raw_knee = self.calculate_angle([p_hip.x, p_hip.y], [p_knee.x, p_knee.y], [p_ankle.x, p_ankle.y])
        knee_angle = self.smooth_value(raw_knee, self.prev_knee_angle)
        self.prev_knee_angle = knee_angle

        p_vertical = [p_hip.x, p_hip.y - 0.5] 
        raw_back = self.calculate_angle([p_shldr.x, p_shldr.y], [p_hip.x, p_hip.y], p_vertical)
        back_angle = self.smooth_value(raw_back, self.prev_back_angle)
        self.prev_back_angle = back_angle

        # Logic
        voice_command = None
        
        if knee_angle > 160:
            self.stage = "UP"
            self.feedback = "SIAP"
            self.feedback_color = (0, 255, 255)
            self.standing_hip_y = p_hip.y
            self.is_calibrated = True
        
        elif knee_angle < 110:
            if back_angle > BACK_FAIL_THRESHOLD:
                self.feedback = "JANGAN BUNGKUK!"
                self.feedback_color = (0, 0, 255)
                voice_command = "Jangan Bungkuk"
            
            elif self.is_calibrated and (p_hip.y - self.standing_hip_y) < HIP_DROP_THRESHOLD:
                self.feedback = "TURUNKAN PINGGUL!"
                self.feedback_color = (0, 0, 255)
                voice_command = "Turunkan Pinggul"
            
            else:
                if self.stage == "UP":
                    self.stage = "DOWN"
                    self.counter += 1
                    self.feedback = "BAGUS!"
                    self.feedback_color = (0, 255, 0)
                    if self.counter % 5 == 0:
                        voice_command = f"{self.counter} Repetisi"
                if self.feedback != "BAGUS!":
                    self.feedback = "TAHAN..."

        return {
            "knee_angle": knee_angle,
            "back_angle": back_angle,
            "p_shldr": p_shldr,
            "p_hip": p_hip,
            "p_knee": p_knee,
            "feedback": self.feedback,
            "feedback_color": self.feedback_color,
            "counter": self.counter,
            "voice_command": voice_command,
            "standing_hip_y": self.standing_hip_y,
            "is_calibrated": self.is_calibrated
        }
