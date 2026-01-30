"""
Updated Bicep Curl exercise script for mediapipe 0.10.x
Uses PoseLandmarker API instead of the deprecated solutions API
"""
import cv2
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import PoseLandmarker, RunningMode
import pyttsx3
import os

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

def calculate_angle(a, b, c):
    """Calculate angle between three points"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

def draw_landmarks_on_image(rgb_image, result):
    """Draw pose landmarks on the image"""
    annotated_image = np.copy(rgb_image)
    
    if result.pose_landmarks:
        # Draw landmarks
        for landmark in result.pose_landmarks:
            x = int(landmark.x * annotated_image.shape[1])
            y = int(landmark.y * annotated_image.shape[0])
            cv2.circle(annotated_image, (x, y), 5, (0, 255, 0), -1)
        
        # Draw connections
        # Define connections for pose
        connections = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (13, 14),  # Upper body
            (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28)  # Lower body
        ]
        
        for connection in connections:
            try:
                start_idx, end_idx = connection
                if start_idx < len(result.pose_landmarks) and end_idx < len(result.pose_landmarks):
                    start = result.pose_landmarks[start_idx]
                    end = result.pose_landmarks[end_idx]
                    start_x = int(start.x * annotated_image.shape[1])
                    start_y = int(start.y * annotated_image.shape[0])
                    end_x = int(end.x * annotated_image.shape[1])
                    end_y = int(end.y * annotated_image.shape[0])
                    cv2.line(annotated_image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)
            except:
                pass
    
    return annotated_image

def main():
    print("Starting Bicep Curl detection...")
    print("Press 'q' to quit")
    
    # Create PoseLandmarker
    base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=RunningMode.LIVE_STREAM,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5
    )
    detector = vision.PoseLandmarker.create_from_options(options)
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Counter variables
    counter = 0
    stage = None
    
    while cap.isOpened():
        success, frame = cap.read()
        
        if not success:
            print("Failed to capture frame")
            break
        
        # Convert BGR to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # Create MediaPipe Image
        mp_image = vision.Image(image_format=vision.ImageFormat.SRGB, data=image)
        
        # Detect pose
        result = detector.detect_for_video(mp_image, int(cap.get(cv2.CAP_PROP_POS_MSEC)))
        
        # Convert back to BGR for display
        annotated_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Draw landmarks
        annotated_image = draw_landmarks_on_image(annotated_image, result)
        
        # Process landmarks
        try:
            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                landmarks = result.pose_landmarks
                
                # Get coordinates for right arm (bicep curl)
                right_shoulder = [landmarks[11].x, landmarks[11].y]
                right_elbow = [landmarks[13].x, landmarks[13].y]
                right_wrist = [landmarks[15].x, landmarks[15].y]
                
                # Calculate angle
                angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
                
                # Visualize angle
                cv2.putText(annotated_image, f'{angle:.1f}°', 
                           (int(right_elbow[0] * annotated_image.shape[1]), 
                            int(right_elbow[1] * annotated_image.shape[0])),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Curl counter logic
                if angle > 160:
                    stage = "down"
                if angle < 40 and stage == "down":
                    stage = "up"
                    counter += 1
                    print(f"Rep: {counter}")
                    speak(str(counter))
        except Exception as e:
            pass
        
        # Draw counter info
        cv2.rectangle(annotated_image, (0, 0), (200, 100), (245, 117, 16), -1)
        cv2.putText(annotated_image, 'REPS', (15, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.putText(annotated_image, str(counter), 
                   (50, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        cv2.putText(annotated_image, f'STAGE: {stage if stage else "waiting"}', (15, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show info
        cv2.putText(annotated_image, 'Bicep Curl Tracker', (10, 470), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated_image, 'Press Q to quit', (10, 495), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        cv2.imshow('Bicep Curl Detection', annotated_image)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released. Windows closed.")

if __name__ == "__main__":
    # Import python module for BaseOptions
    from mediapipe.tasks.python import python
    main()

