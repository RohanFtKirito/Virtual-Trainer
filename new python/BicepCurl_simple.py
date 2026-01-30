"""
Simple Bicep Curl Tracker using basic computer vision
Works without MediaPipe dependency
"""
import cv2
import numpy as np
import pyttsx3

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak(msg):
    """Speak a message using text-to-speech"""
    try:
        engine.say(msg)
        engine.runAndWait()
    except:
        pass

def nothing(x):
    """Empty callback for trackbars"""
    pass

def main():
    print("Starting Bicep Curl Tracker...")
    print("Camera warming up...")
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Get initial frame to set up
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture initial frame")
        return
    
    # Convert to grayscale for motion detection
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
    
    # Counter variables
    counter = 0
    stage = None
    arm_position = "down"  # Track arm position based on motion
    
    print("Ready! Press 'q' to quit")
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to capture frame")
            break
        
        # Display the frame
        display = frame.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Calculate motion difference
        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for motion in the upper body area (where biceps are)
        height, width = frame.shape[:2]
        upper_region = thresh[0:int(height*0.6), :]
        
        # Calculate motion intensity in upper region
        motion_score = cv2.countNonZero(upper_region)
        
        # Simple state machine for bicep curl counting
        if motion_score > 5000:  # Significant motion detected
            if arm_position == "down":
                arm_position = "moving_up"
        elif motion_score < 1000:  # Motion stopped
            if arm_position == "moving_up":
                arm_position = "up"
                counter += 1
                print(f"Rep: {counter}")
                speak(str(counter))
            elif arm_position == "up":
                arm_position = "moving_down"
        else:
            if arm_position == "moving_down":
                arm_position = "down"
        
        # Draw UI elements
        cv2.rectangle(display, (0, 0), (220, 100), (245, 117, 16), -1)
        cv2.putText(display, 'REPS', (15, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(display, str(counter), 
                   (50, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        cv2.putText(display, f'STAGE: {arm_position}', (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.putText(display, 'Bicep Curl Tracker', (10, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, 'Motion detected: ' + str(motion_score), (10, 475), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(display, 'Press Q to quit', (10, 500), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw motion visualization
        cv2.rectangle(display, (width-150, height-80), (width-10, height-10), (0, 0, 0), -1)
        motion_bar = min(int(motion_score / 50), 130)
        cv2.rectangle(display, (width-145, height-75), (width-145 + motion_bar, height-15), 
                     (0, 255, 0) if motion_score < 5000 else (0, 0, 255), -1)
        cv2.putText(display, 'Motion', (width-145, height-85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Show frame
        cv2.imshow('Bicep Curl Tracker', display)
        
        # Update previous frame
        prev_gray = gray
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Session complete! Total reps: {counter}")

if __name__ == "__main__":
    main()

