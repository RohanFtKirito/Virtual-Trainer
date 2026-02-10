"""
Bicep Curl Tracker with Motion Detection and Voice Feedback
"""

import cv2
import numpy as np
import pyttsx3


def main():
    print("=" * 50)
    print("BICEP CURL TRACKER")
    print("=" * 50)
    print("Instructions:")
    print("- Position yourself so your upper body is visible")
    print("- Do bicep curls - the motion will be detected")
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

    # Initialize motion tracking
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture initial frame")
        return

    # Resize for faster processing (KEEPING YOUR ORIGINAL SIZE)
    frame = cv2.resize(frame, (640, 480))
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

    # Rep counting variables
    counter = 0
    stage = "down"

    print("Ready! Press 'q' to quit.\n")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Failed to capture frame")
            break

        # Resize frame
        frame = cv2.resize(frame, (640, 480))
        display = frame.copy()

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Motion detection
        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Upper body region focus
        height, width = display.shape[:2]
        upper_region = thresh[0:int(height * 0.6), :]

        # Motion score calculation
        motion_score = cv2.countNonZero(upper_region)

        # ---------------- STATE MACHINE (UNCHANGED) ----------------
        if motion_score > 3000:
            if stage == "down":
                stage = "moving"

        elif motion_score < 500:
            if stage == "moving":
                stage = "up"

        else:
            if stage == "up":
                stage = "completing"

        if stage == "completing" and motion_score < 300:
            counter += 1
            stage = "down"
            print(f"Rep counted! Total: {counter}")
            # Voice feedback for each rep
            speak(counter)
            print("Voice Triggered for Rep:", counter)

        # ---------------- UI ----------------
        cv2.rectangle(display, (0, 0), (220, 120), (245, 117, 16), -1)

        cv2.putText(display, 'REPS', (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        cv2.putText(display, str(counter),
                    (50, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

        stage_text = stage.upper() if stage != "completing" else "ALMOST!"
        cv2.putText(display, f'STAGE: {stage_text}', (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.putText(display, 'Bicep Curl Tracker', (10, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(display, 'Motion detected: ' + str(motion_score), (10, 475),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.putText(display, 'Press Q to quit', (10, 495),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Motion bar
        cv2.rectangle(display, (width - 160, height - 50), (width - 10, height - 10), (0, 0, 0), -1)

        motion_bar = min(int(motion_score / 50), 140)

        color = (
            (0, 255, 0) if motion_score < 3000
            else (0, 165, 255) if motion_score < 8000
            else (0, 0, 255)
        )

        cv2.rectangle(display, (width - 155, height - 45),
                      (width - 155 + motion_bar, height - 15), color, -1)

        cv2.putText(display, 'Motion', (width - 155, height - 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        cv2.imshow('Bicep Curl Tracker', display)

        # Update previous frame
        prev_gray = gray

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\nSession complete!")
    print(f"Total reps: {counter}")


if __name__ == "__main__":
    main()

