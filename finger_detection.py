import cv2
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp

class FingerDetector:
    def __init__(self, model_path="hand_landmarker.task"):
        """Initialize the finger detection system using MediaPipe 0.10+ API."""
        import os
        
        # Check if model file exists, download if not
        if not os.path.exists(model_path):
            print(f"Model file not found. Please download hand_landmarker.task")
            print("Download from: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Initialize hand landmarker for video mode with higher confidence
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.7,  # Increased for better accuracy
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # For static images
        base_options_image = python.BaseOptions(model_asset_path=model_path)
        options_image = vision.HandLandmarkerOptions(
            base_options=base_options_image,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector_image = vision.HandLandmarker.create_from_options(options_image)
        
        self.frame_timestamp_ms = 0
        self.use_smoothing = True
        # Smoothing buffer for finger counts (reduces jitter)
        self.count_history = []
        self.history_size = 5
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (5, 9), (9, 13), (13, 17)  # Palm connections
        ]
        
    def count_fingers(self, landmarks, debug=False):
        """
        Count the number of raised fingers with improved accuracy.
        Uses distance-based checks for more reliable detection.
        Returns: count (int) - number of fingers raised
        """
        # MediaPipe hand landmarks (21 points per hand):
        # Thumb: tip(4), IP(3), MCP(2), CMC(1)
        # Index: tip(8), PIP(6), MCP(5)
        # Middle: tip(12), PIP(10), MCP(9)
        # Ring: tip(16), PIP(14), MCP(13)
        # Pinky: tip(20), PIP(18), MCP(17)
        # Wrist: 0
        
        fingers = []
        finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        wrist = landmarks[0]
        
        # Thumb detection - check if extended outward from hand
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        index_mcp = landmarks[5]
        
        # Method 1: Check if thumb tip is to the right of thumb IP (for right hand)
        # Method 2: Check distance from wrist
        thumb_to_right = thumb_tip.x > thumb_ip.x + 0.02  # Thumb extended right
        thumb_distance = ((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)**0.5
        thumb_mcp_distance = ((thumb_mcp.x - wrist.x)**2 + (thumb_mcp.y - wrist.y)**2)**0.5
        
        # Thumb is extended if it's clearly to the side OR far from wrist
        thumb_extended = thumb_to_right or (thumb_distance > thumb_mcp_distance * 1.15)
        fingers.append(1 if thumb_extended else 0)
        
        if debug:
            print(f"Thumb: extended={thumb_extended}, to_right={thumb_to_right}, dist_ratio={thumb_distance/thumb_mcp_distance:.2f}")
        
        # For other 4 fingers: Check if tip is above MCP joint
        # Use a threshold to prevent false positives from slightly bent fingers
        
        finger_checks = [
            (8, 5, 6),   # Index: tip, MCP, PIP
            (12, 9, 10), # Middle: tip, MCP, PIP
            (16, 13, 14), # Ring: tip, MCP, PIP
            (20, 17, 18) # Pinky: tip, MCP, PIP
        ]
        
        for i, (tip_idx, mcp_idx, pip_idx) in enumerate(finger_checks):
            tip = landmarks[tip_idx]
            mcp = landmarks[mcp_idx]
            pip = landmarks[pip_idx]
            
            # Check if tip is above MCP (finger is raised)
            # Also verify tip is above PIP to ensure finger is extended, not just bent
            tip_above_mcp = tip.y < mcp.y
            tip_above_pip = tip.y < pip.y
            
            # Finger is raised if tip is above MCP AND tip is above PIP
            # This ensures the finger is truly extended, not just bent at the base
            finger_raised = tip_above_mcp and tip_above_pip
            
            fingers.append(1 if finger_raised else 0)
            
            if debug:
                print(f"{finger_names[i+1]}: raised={finger_raised}, tip_y={tip.y:.3f}, mcp_y={mcp.y:.3f}, pip_y={pip.y:.3f}")
        
        total = sum(fingers)
        
        # Apply smoothing to reduce jitter
        if self.use_smoothing:
            self.count_history.append(total)
            if len(self.count_history) > self.history_size:
                self.count_history.pop(0)
            # Return the most common value in recent history
            from collections import Counter
            if len(self.count_history) >= 3:
                most_common = Counter(self.count_history).most_common(1)[0][0]
                return most_common
        
        return total
    
    def draw_landmarks(self, image, landmarks):
        """Draw hand landmarks and connections on the image."""
        h, w, c = image.shape
        
        # Draw connections
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start_point = (int(landmarks[start_idx].x * w),
                          int(landmarks[start_idx].y * h))
            end_point = (int(landmarks[end_idx].x * w),
                        int(landmarks[end_idx].y * h))
            cv2.line(image, start_point, end_point, (0, 255, 0), 2)
        
        # Draw landmarks
        for landmark in landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
    
    def detect_from_image(self, image_path):
        """
        Detect and count fingers from a static image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            image: Image with annotations
            finger_count: Number of fingers detected
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return None, 0
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Detect hands
        detection_result = self.detector_image.detect(mp_image)
        
        finger_count = 0
        
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                # Draw hand landmarks
                self.draw_landmarks(image, hand_landmarks)
                
                # Count fingers
                count = self.count_fingers(hand_landmarks)
                finger_count += count
                
                # Get hand position for text
                h, w, c = image.shape
                x = int(hand_landmarks[0].x * w)
                y = int(hand_landmarks[0].y * h)
                
                # Display finger count
                cv2.putText(image, f'Fingers: {count}', (x, y - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return image, finger_count
    
    def detect_from_camera(self):
        """
        Real-time finger detection from live camera feed.
        Press 'q' to quit.
        """
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        print("Starting finger detection...")
        print("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            
            # Detect hands
            detection_result = self.detector.detect_for_video(mp_image, self.frame_timestamp_ms)
            self.frame_timestamp_ms += 33  # ~30 FPS
            
            total_fingers = 0
            
            if detection_result.hand_landmarks:
                for hand_landmarks in detection_result.hand_landmarks:
                    # Draw hand landmarks
                    self.draw_landmarks(frame, hand_landmarks)
                    
                    # Count fingers
                    count = self.count_fingers(hand_landmarks)
                    total_fingers += count
                    
                    # Get hand position for text
                    h, w, c = frame.shape
                    x = int(hand_landmarks[0].x * w)
                    y = int(hand_landmarks[0].y * h)
                    
                    # Display finger count
                    cv2.putText(frame, f'Fingers: {count}', (x, y - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display total finger count at top
            cv2.putText(frame, f'Total Fingers: {total_fingers}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # Display tips for better accuracy
            cv2.putText(frame, "Tip: Keep hand steady, good lighting", (10, frame.shape[0] - 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            # Display individual finger status (optional - for debugging)
            finger_status = []
            for i, hand_landmarks in enumerate(detection_result.hand_landmarks):
                count = self.count_fingers(hand_landmarks, debug=False)
                finger_status.append(f"Hand {i+1}: {count}")
            
            if len(finger_status) > 0:
                cv2.putText(frame, " | ".join(finger_status), (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Display instructions
            cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Finger Detection', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("Finger detection stopped.")


def main():
    """Main function to run finger detection."""
    detector = FingerDetector()
    
    print("Finger Detection System")
    print("=" * 30)
    print("1. Detect from image")
    print("2. Detect from live camera")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == '1':
        image_path = input("Enter image path: ").strip()
        image, count = detector.detect_from_image(image_path)
        
        if image is not None:
            print(f"\nDetected {count} finger(s)")
            cv2.imshow('Finger Detection Result', image)
            print("Press any key to close...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    elif choice == '2':
        detector.detect_from_camera()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
