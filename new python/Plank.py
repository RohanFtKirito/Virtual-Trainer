import pyttsx3
import cv2
import mediapipe as mp
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0)

cv2.namedWindow('Mediapipe Feed', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Mediapipe Feed', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# -------- ANGLE FUNCTION --------
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle

    return angle

stage = None
flag = 0


def main():
    # Initialize pyttsx3 engine inside main() for better Mac compatibility
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if len(voices) > 0:
        engine.setProperty('voice', voices[0].id)

    def speak(msg):
        engine.say(str(msg))
        engine.runAndWait()

    # Debug voice test to confirm engine is working
    speak("Exercise started")

    stage = None
    flag = 0

    with mp_pose.Pose(min_detection_confidence=0.5,
                      min_tracking_confidence=0.5) as pose:

        while cap.isOpened():

            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                if results.pose_landmarks:

                    landmarks = results.pose_landmarks.landmark

                    shoulder = [landmarks[11].x, landmarks[11].y]
                    elbow = [landmarks[13].x, landmarks[13].y]
                    wrist = [landmarks[15].x, landmarks[15].y]
                    hip = [landmarks[23].x, landmarks[23].y]
                    knee = [landmarks[25].x, landmarks[25].y]

                    angle1 = calculate_angle(shoulder, elbow, wrist)
                    angle2 = calculate_angle(shoulder, hip, knee)

                    cv2.putText(image, str(int(angle1)),
                                tuple(np.multiply(elbow, [w, h]).astype(int)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

                    cv2.putText(image, str(int(angle2)),
                                tuple(np.multiply(hip, [w, h]).astype(int)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

                    # Plank Logic (UNCHANGED)
                    if 80 < angle1 < 100 and 170 < angle2 < 190:
                        stage = "perfect"
                    else:
                        stage = "wrong"

                    if flag == 0 and stage == "perfect":
                        speak("perfect")
                        flag = 1
                    elif flag == 1 and stage == "wrong":
                        speak("wrong")
                        flag = 0

            except Exception as e:
                print("Pose error:", e)

            # UI
            cv2.rectangle(image, (0, 0), (225, 73), (245, 117, 16), -1)

            cv2.putText(image, 'STAGE', (65, 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            cv2.putText(image, str(stage),
                        (60, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

            cv2.imshow('Mediapipe Feed', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

