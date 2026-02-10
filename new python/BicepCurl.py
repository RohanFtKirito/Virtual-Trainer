import pyttsx3
import cv2
import mediapipe as mp
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# ---------------- ANGLE FUNCTION ----------------
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)

    if angle > 180:
        angle = 360 - angle

    return angle

# ---------------- TEXT TO SPEECH SETUP (MOVED OUTSIDE LOOP) ----------------
engine = pyttsx3.init()
voices = engine.getProperty("voices")
if len(voices) > 1:
    engine.setProperty("voice", voices[1].id)

def speak(msg):
    engine.say(str(msg))
    engine.runAndWait()

# ---------------- WINDOW SETUP ----------------
cv2.namedWindow('Mediapipe Feed', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Mediapipe Feed', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cap = cv2.VideoCapture(0)

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Camera resolution: {frame_width}x{frame_height}")

# ---------------- COUNTER VARIABLES ----------------
counter = 0
stage = None

# ---------------- MEDIAPIPE POSE ----------------
with mp_pose.Pose(min_detection_confidence=0.5,
                  min_tracking_confidence=0.5) as pose:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        results = pose.process(image)

        # Back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            if results.pose_landmarks:

                landmarks = results.pose_landmarks.landmark

                shoulder = [
                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
                ]
                elbow = [
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y
                ]
                wrist = [
                    landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y
                ]

                # Calculate angle
                angle = calculate_angle(shoulder, elbow, wrist)

                # Show angle
                cv2.putText(
                    image,
                    str(round(angle, 2)),
                    tuple(np.multiply(elbow, [frame_width, frame_height]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA
                )

                # ---------------- REP LOGIC (UNCHANGED) ----------------
                if angle > 160:
                    stage = "down"

                if angle < 30 and stage == 'down':
                    stage = "up"
                    counter += 1
                    print(counter)
                    speak(counter)

        except Exception as e:
            print("Landmark error:", e)

        # ---------------- UI BOX ----------------
        cv2.rectangle(image, (0, 0), (260, 73), (245, 117, 16), -1)

        # Rep UI
        cv2.putText(image, 'REPS', (15, 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        cv2.putText(image, str(counter),
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        # Stage UI
        cv2.putText(image, 'STAGE', (105, 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        cv2.putText(image, str(stage),
                    (100, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

        # Draw landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 31, 63), thickness=2, circle_radius=2)
            )

        cv2.imshow('Mediapipe Feed', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()