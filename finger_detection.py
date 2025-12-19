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
        
        # Initialize hand landmarker for video mode
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # For static images
        base_options_image = python.BaseOptions(model_asset_path=model_path)
        options_image = vision.HandLandmarkerOptions(
            base_options=base_options_image,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector_image = vision.HandLandmarker.create_from_options(options_image)
        
        self.frame_timestamp_ms = 0
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (5, 9), (9, 13), (13, 17)  # Palm connections
        ]
        
    def count_fingers(self, landmarks):
        """
        Count the number of raised fingers with high accuracy.
        Uses multiple checks: MCP joints and PIP joints for reliability.
        Returns: count (int) - number of fingers raised
        """
        # MediaPipe hand landmarks (21 points per hand):
        # Thumb: tip(4), IP(3), MCP(2)
        # Index: tip(8), PIP(6), MCP(5)
        # Middle: tip(12), PIP(10), MCP(9)
        # Ring: tip(16), PIP(14), MCP(13)
        # Pinky: tip(20), PIP(18), MCP(17)
        # Wrist: 0
        
        fingers = []
        
        # Thumb detection (special case - moves differently)
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        wrist = landmarks[0]
        
        # Calculate distances to determine thumb position
        # Thumb is extended if tip is clearly away from hand
        thumb_tip_to_ip_x = abs(thumb_tip.x - thumb_ip.x)
        thumb_tip_to_ip_y = abs(thumb_tip.y - thumb_ip.y)
        thumb_ip_to_mcp_x = abs(thumb_ip.x - thumb_mcp.x)
        
        # Thumb is extended if:
        # 1. Tip is significantly further from IP joint horizontally, OR
        # 2. Tip is above IP joint (pointing up)
        thumb_extended = (thumb_tip_to_ip_x > thumb_ip_to_mcp_x * 1.2) or \
                        (thumb_tip.y < thumb_ip.y - 0.015)
        fingers.append(1 if thumb_extended else 0)
        
        # For other 4 fingers: Use both MCP and PIP checks for accuracy
        # A finger is raised only if BOTH conditions are met:
        # 1. Tip is above MCP joint (base of finger)
        # 2. Tip is above PIP joint (middle joint) - ensures finger is truly extended
        
        # Index finger
        index_tip_above_mcp = landmarks[8].y < landmarks[5].y
        index_tip_above_pip = landmarks[8].y < landmarks[6].y
        fingers.append(1 if (index_tip_above_mcp and index_tip_above_pip) else 0)
        
        # Middle finger
        middle_tip_above_mcp = landmarks[12].y < landmarks[9].y
        middle_tip_above_pip = landmarks[12].y < landmarks[10].y
        fingers.append(1 if (middle_tip_above_mcp and middle_tip_above_pip) else 0)
        
        # Ring finger
        ring_tip_above_mcp = landmarks[16].y < landmarks[13].y
        ring_tip_above_pip = landmarks[16].y < landmarks[14].y
        fingers.append(1 if (ring_tip_above_mcp and ring_tip_above_pip) else 0)
        
        # Pinky finger
        pinky_tip_above_mcp = landmarks[20].y < landmarks[17].y
        pinky_tip_above_pip = landmarks[20].y < landmarks[18].y
        fingers.append(1 if (pinky_tip_above_mcp and pinky_tip_above_pip) else 0)
        
        return sum(fingers)
    
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
