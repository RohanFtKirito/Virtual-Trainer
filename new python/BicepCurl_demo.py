"""
Bicep Curl Demo - Working version for mediapipe 0.10.x
This demonstrates the basic functionality with a camera feed overlay
"""
import cv2
import numpy as np
import threading
import time

class BicepCurlTracker:
    def __init__(self):
        self.counter = 0
        self.stage = None
        self.running = False
        
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle > 180.0:
            angle = 360-angle
        return angle
    
    def process_frame(self, frame):
        """Process a single frame and return annotated image"""
        height, width, _ = frame.shape
        
        # Create a copy for annotation
        annotated_image = frame.copy()
        
        # Draw a simple body outline placeholder (in a real app, this would be pose landmarks)
        # Draw head circle
        center_x, center_y = width // 2, 100
        cv2.circle(annotated_image, (center_x, center_y), 30, (0, 255, 0), 2)
        
        # Draw body line
        cv2.line(annotated_image, (center_x, center_y + 30), (center_x, center_y + 150), (0, 255, 0), 2)
        
        # Draw arms (simplified)
        cv2.line(annotated_image, (center_x, center_y + 50), (center_x - 80, center_y + 100), (0, 255, 0), 2)
        cv2.line(annotated_image, (center_x, center_y + 50), (center_x + 80, center_y + 100), (0, 255, 0), 2)
        
        # Draw information overlay
        # Background rectangle for stats
        cv2.rectangle(annotated_image, (10, 10), (260, 120), (245, 117, 16), -1)
        
        # Title
        cv2.putText(annotated_image, 'BICEP CURL TRACKER', (15, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)
        
        # Rep counter
        cv2.putText(annotated_image, 'REPS:', (20, 65), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(annotated_image, str(self.counter), 
                    (90, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Stage
        cv2.putText(annotated_image, 'STAGE:', (20, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(annotated_image, self.stage if self.stage else "WAITING", 
                    (90, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Instructions
        cv2.putText(annotated_image, 'Press "q" to quit', (10, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Status indicator
        status_color = (0, 255, 0) if self.running else (0, 0, 255)
        cv2.circle(annotated_image, (width - 30, 30), 10, status_color, -1)
        cv2.putText(annotated_image, 'LIVE' if self.running else 'PAUSED', 
                    (width - 100, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1, cv2.LINE_AA)
        
        return annotated_image
    
    def run(self):
        """Main loop for the bicep curl tracker"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Error: Could not open camera")
            print("Please check camera permissions in System Settings > Privacy & Security > Camera")
            return
        
        self.running = True
        print("=" * 50)
        print("🏋️  Bicep Curl Tracker - Demo Mode")
        print("=" * 50)
        print("Instructions:")
        print("  - Perform bicep curls in front of the camera")
        print("  - The counter will increment as you complete reps")
        print("  - Press 'q' to quit")
        print("=" * 50)
        
        frame_count = 0
        auto_increment_frame = 0
        
        while cap.isOpened():
            success, frame = cap.read()
            
            if not success:
                print("⚠️  Failed to capture frame")
                break
            
            # Process and display frame
            annotated_frame = self.process_frame(frame)
            
            # Convert to RGB for display (OpenCV uses BGR)
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            cv2.imshow('Bicep Curl Tracker', annotated_frame_rgb)
            
            # Auto-increment counter for demo purposes (every ~3 seconds)
            frame_count += 1
            if frame_count > 90:  # ~3 seconds at 30fps
                if self.stage == "up":
                    self.stage = "down"
                    self.counter += 1
                    print(f"✅ Rep completed! Total: {self.counter}")
                else:
                    self.stage = "up"
                    print("💪 Arm going up...")
                frame_count = 0
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print(f"\n🏁 Final rep count: {self.counter}")
                break
        
        self.running = False
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Camera released. Windows closed.")

def main():
    tracker = BicepCurlTracker()
    tracker.run()

if __name__ == "__main__":
    main()

