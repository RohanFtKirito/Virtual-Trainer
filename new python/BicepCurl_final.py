"""
Bicep Curl Tracker with Motion Detection
Works with any OpenCV version - no mediapipe dependency
"""
import cv2
import numpy as np
import os

def speak(msg):
    """Simple feedback - displays on screen"""
    pass  # Text-to-speech requires additional setup

def main():
    print("=" * 50)
    print("BICEP CURL TRACKER")
    print("=" * 50)
    print("Instructions:")
    print("- Position yourself so your upper body is visible")
    print("- Do bicep curls - the motion will be detected")
    print("- A counter will appear showing your reps")
    print("- Press 'q' to quit")
    print("=" * 50)
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open camera!")
        print("Please check camera permissions in System Settings > Privacy > Camera")
        input("Press Enter to exit...")
        return
    
    print("\nCamera opened successfully!")
    print("Starting detection...\n")
    
    # Initialize motion tracking
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture initial frame")
        return
    
    # Resize for faster processing
    frame = cv2.resize(frame, (640, 480))
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
    
    # Rep counting variables
    counter = 0
    stage = "down"  # down -> up -> down = 1 rep
    last_motion_time = 0
    
    print("Ready! Press 'q' to quit.\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break
        
        # Resize and process
        frame = cv2.resize(frame, (640, 480))
        display = frame.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Calculate motion difference
        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours of motion
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Focus on upper body region (where arm curls happen)
        height, width = display.shape[:2]
        upper_region = thresh[0:int(height*0.6), :]
        
        # Calculate motion in upper region
        motion_score = cv2.countNonZero(upper_region)
        
        # State machine for rep counting
        # Motion in upper region = arm moving
        if motion_score > 3000:  # Significant motion detected
            if stage == "down":
                stage = "moving"
        elif motion_score < 500:  # Motion stopped
            if stage == "moving":
                stage = "up"
        else:
            # Motion decreasing - arm coming down
            if stage == "up":
                stage = "completing"
        
        # Count rep when cycle completes
        if stage == "completing" and motion_score < 300:
            counter += 1
            stage = "down"
            print(f"Rep counted! Total: {counter}")
        
        # Draw motion visualization
        cv2.rectangle(display, (0, 0), (220, 120), (245, 117, 16), -1)
        cv2.putText(display, 'REPS', (15, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(display, str(counter), 
                   (50, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Stage indicator
        stage_text = stage.upper() if stage != "completing" else "ALMOST!"
        cv2.putText(display, f'STAGE: {stage_text}', (10, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Instructions
        cv2.putText(display, 'Bicep Curl Tracker', (10, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, 'Motion detected: ' + str(motion_score), (10, 475), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(display, 'Press Q to quit', (10, 495), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Motion bar
        cv2.rectangle(display, (width-160, height-50), (width-10, height-10), (0, 0, 0), -1)
        motion_bar = min(int(motion_score / 50), 140)
        color = (0, 255, 0) if motion_score < 3000 else (0, 165, 255) if motion_score < 8000 else (0, 0, 255)
        cv2.rectangle(display, (width-155, height-45), (width-155 + motion_bar, height-15), color, -1)
        cv2.putText(display, 'Motion', (width-155, height-55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Show frame
        cv2.imshow('Bicep Curl Tracker', display)
        
        # Update previous frame
        prev_gray = gray
        
        # Quit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nSession complete!")
    print(f"Total reps: {counter}")

if __name__ == "__main__":
    main()

