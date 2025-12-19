# Finger Detection System

A real-time finger detection and counting system using OpenCV and MediaPipe. This system can detect and count fingers (1, 2, 3, 4, 5) from both static images and live camera feeds.

## Features

- ✅ Real-time finger detection from live camera feed
- ✅ Finger detection from static images
- ✅ Finger counting (1-5 per hand, supports both hands)
- ✅ Visual landmarks and connections displayed
- ✅ Can be extended to face tracking (as mentioned)

## Requirements

- Python 3.7+
- Webcam (for live detection)
- OpenCV
- MediaPipe
- NumPy

## Installation

1. Create a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Download the hand landmarker model file:

The model file will be automatically downloaded when you first run the script, or you can download it manually:

```bash
curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

The model file (`hand_landmarker.task`) should be in the same directory as `finger_detection.py`.

## Usage

### Activate the virtual environment (if using one):

```bash
source venv/bin/activate  # On macOS/Linux
```

### Run the application:

```bash
python finger_detection.py
# or
python3 finger_detection.py
```

### Options:

1. **Detect from Image**: Provide a path to an image file containing a hand
2. **Detect from Live Camera**: Uses your webcam for real-time detection

### Controls:

- Press **'q'** to quit when using live camera mode

## How It Works

The system uses MediaPipe's hand detection model to:

1. Detect hand landmarks (21 points per hand)
2. Analyze finger tip positions relative to joint positions
3. Count raised fingers based on coordinate comparisons
4. Display the count and hand landmarks on the screen

## Extending to Face Tracking

To extend this to face tracking, you can:

1. Use MediaPipe's face detection: `mp.solutions.face_detection`
2. Use MediaPipe's face mesh: `mp.solutions.face_mesh`
3. Integrate with OpenCV's Haar Cascades for face detection

## Example

The system will display:

- Hand landmarks and connections
- Finger count per hand
- Total finger count (if multiple hands detected)

## Notes

- Works best with good lighting
- Keep hands clearly visible in the frame
- Supports up to 2 hands simultaneously
