"""
PushUp Counter with MediaPipe Pose Detection and Voice Feedback
"""

import cv2
import mediapipe as mp
import pyttsx3
import os


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

counter = 0
stage = None
create = None
opname = "output.avi"


def findPosition(image, draw=True):
    lmList = []
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        for id, lm in enumerate(results.pose_landmarks.landmark):
            h, w, c = image.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            lmList.append([id, cx, cy])
    return lmList


def main():
    print("=" * 50)
    print("PUSHUP COUNTER")
    print("=" * 50)
    print("Instructions:")
    print("- Position yourself so your upper body is visible")
    print("- Do pushups - pose will be detected")
    print("- A counter will appear showing your reps")
    print("- Voice will announce each rep count")
    print("- Press 'q' to quit")
    print("=" * 50)

    # Open camera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open camera!")
        input("Press Enter to exit...")
        return

    print("\nCamera opened successfully!")
    print("Starting detection...\n")

    # Initialize pyttsx3 engine inside main() for better Mac compatibility
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if len(voices) > 0:
        engine.setProperty('voice', voices[0].id)

    def speak(msg):
        """Text-to-speech feedback"""
        engine.say(str(msg))
        engine.runAndWait()

    # Debug voice test to confirm engine is working
    speak("Exercise started")

    counter = 0
    stage = None

    with mp_pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as pose:

        while cap.isOpened():
            success, image = cap.read()
            image = cv2.resize(image, (640, 480))

            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip the image horizontally for selfie-view display
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

            # To improve performance, mark image as not writeable
            results = pose.process(image)

            # Draw pose annotation on the image
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            lmList = findPosition(image, draw=True)

            if len(lmList) != 0:
                # Draw landmarks on image
                cv2.circle(image, (lmList[12][1], lmList[12][2]), 20, (0, 0, 255), cv2.FILLED)
                cv2.circle(image, (lmList[11][1], lmList[11][2]), 20, (0, 0, 255), cv2.FILLED)

                # Check for up position (elbows above shoulders)
                if (lmList[12][2] and lmList[11][2] >= lmList[14][2] and lmList[13][2]):
                    cv2.circle(image, (lmList[12][1], lmList[12][2]), 20, (0, 255, 0), cv2.FILLED)
                    cv2.circle(image, (lmList[11][1], lmList[11][2]), 20, (0, 255, 0), cv2.FILLED)
                    stage = "down"

                # Check for down position and count rep
                if (lmList[12][2] and lmList[11][2] <= lmList[14][2] and lmList[13][2]) and stage == "down":
                    stage = "up"
                    counter += 1
                    print(f"PushUp count: {counter}")
                    # Voice feedback for each rep
                    speak(counter)
                    print("Voice Triggered for Rep:", counter)

            text = "{}:{}".format("Push Ups", counter)

            cv2.putText(image, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 0, 0), 2)

            cv2.imshow('MediaPipe Pose', image)

            if create is None:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                create = cv2.VideoWriter(opname, fourcc, 30, (image.shape[1], image.shape[0]), True)

            create.write(image)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    print("\nSession complete!")
    print(f"Total pushups: {counter}")


if __name__ == "__main__":
    main()

