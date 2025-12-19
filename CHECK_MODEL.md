# Commands to Check if AI Model Exists on MacBook

## 🔍 Quick Check Commands

### 1. Check if Model File Exists (Current Directory)

```bash
ls -lh hand_landmarker.task
```

**What it shows:**

- File size (should be ~7.5M)
- File permissions
- Last modified date
- File name

**Example Output:**

```
-rw-r--r--  1 nyfong  staff   7.5M Dec 19 13:56 hand_landmarker.task
```

---

### 2. Check if Model File Exists (Anywhere)

```bash
find ~ -name "hand_landmarker.task" 2>/dev/null
```

**What it does:**

- Searches entire home directory
- Finds all instances of the file
- Shows full paths

**Example Output:**

```
/Users/nyfong/rootcoding/RUPP/AI Y4/hand_landmarker.task
```

---

### 3. Check File Size and Details

```bash
ls -lh hand_landmarker.task && file hand_landmarker.task
```

**What it shows:**

- File size in human-readable format
- File type/format

**Example Output:**

```
-rw-r--r--  1 nyfong  staff   7.5M Dec 19 13:56 hand_landmarker.task
hand_landmarker.task: data
```

---

### 4. Verify Model File is Valid (Check Size)

```bash
if [ -f "hand_landmarker.task" ]; then
    size=$(ls -lh hand_landmarker.task | awk '{print $5}')
    echo "✓ Model found! Size: $size"
    if [[ $size == *"7.5M"* ]] || [[ $size == *"7."*"M"* ]]; then
        echo "✓ Size looks correct (~7.5 MB)"
    else
        echo "⚠ Warning: Size seems unusual"
    fi
else
    echo "✗ Model file not found in current directory"
fi
```

---

### 5. Check from Python Script

```bash
python3 -c "
import os
model_path = 'hand_landmarker.task'
if os.path.exists(model_path):
    size = os.path.getsize(model_path) / (1024 * 1024)  # Convert to MB
    print(f'✓ Model found!')
    print(f'  Location: {os.path.abspath(model_path)}')
    print(f'  Size: {size:.2f} MB')
    if 7.0 <= size <= 8.0:
        print('  ✓ Size is correct (~7.5 MB)')
    else:
        print(f'  ⚠ Warning: Size is {size:.2f} MB (expected ~7.5 MB)')
else:
    print('✗ Model file not found')
    print('  Download it using:')
    print('  curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task')
"
```

---

### 6. Complete Check Script

```bash
#!/bin/bash
echo "🔍 Checking for hand_landmarker.task model..."
echo ""

# Check in current directory
if [ -f "hand_landmarker.task" ]; then
    echo "✓ Model found in current directory!"
    ls -lh hand_landmarker.task
    echo ""

    # Check size
    size=$(stat -f%z hand_landmarker.task 2>/dev/null || stat -c%s hand_landmarker.task 2>/dev/null)
    size_mb=$(echo "scale=2; $size / 1024 / 1024" | bc)
    echo "  Size: $size_mb MB"

    if (( $(echo "$size_mb >= 7.0 && $size_mb <= 8.0" | bc -l) )); then
        echo "  ✓ Size is correct!"
    else
        echo "  ⚠ Warning: Size seems unusual"
    fi
else
    echo "✗ Model not found in current directory"
    echo ""
    echo "Searching in home directory..."
    found=$(find ~ -name "hand_landmarker.task" 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        echo "✓ Found at: $found"
        ls -lh "$found"
    else
        echo "✗ Model not found anywhere"
        echo ""
        echo "To download, run:"
        echo "curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    fi
fi
```

---

## 📋 Step-by-Step Verification

### Step 1: Navigate to Project Directory

```bash
cd "/Users/nyfong/rootcoding/RUPP/AI Y4"
```

### Step 2: Check if File Exists

```bash
ls hand_landmarker.task
```

**If file exists:**

```
hand_landmarker.task
```

**If file doesn't exist:**

```
ls: hand_landmarker.task: No such file or directory
```

### Step 3: Verify File Size

```bash
ls -lh hand_landmarker.task
```

**Expected output:**

```
-rw-r--r--  1 nyfong  staff   7.5M Dec 19 13:56 hand_landmarker.task
```

### Step 4: Test if Model Works

```bash
python3 -c "
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

if os.path.exists('hand_landmarker.task'):
    print('✓ Model file exists')
    try:
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1
        )
        detector = vision.HandLandmarker.create_from_options(options)
        print('✓ Model loaded successfully!')
        print('✓ AI model is working correctly')
    except Exception as e:
        print(f'✗ Error loading model: {e}')
else:
    print('✗ Model file not found')
"
```

---

## 🖥️ MacBook-Specific Commands

### Check System Information

```bash
# Check macOS version
sw_vers

# Check Python version
python3 --version

# Check if MediaPipe is installed
python3 -c "import mediapipe; print(f'MediaPipe version: {mediapipe.__version__}')"
```

### Check Disk Space (to ensure you have room)

```bash
df -h .
```

### Check File Permissions

```bash
ls -la hand_landmarker.task
```

---

## ✅ Quick Verification Checklist

Run these commands in order:

```bash
# 1. Check if file exists
[ -f "hand_landmarker.task" ] && echo "✓ File exists" || echo "✗ File not found"

# 2. Check file size
ls -lh hand_landmarker.task | awk '{print "Size: " $5}'

# 3. Check file location
pwd && echo "File: $(pwd)/hand_landmarker.task"

# 4. Test model loading
python3 -c "from mediapipe.tasks import python; from mediapipe.tasks.python import vision; import os; print('✓ Model can be loaded' if os.path.exists('hand_landmarker.task') else '✗ Model missing')"
```

---

## 🚨 Troubleshooting

### If Model Not Found:

1. **Check current directory:**

   ```bash
   pwd
   ls -la | grep hand
   ```

2. **Search for it:**

   ```bash
   find ~ -name "hand_landmarker.task" 2>/dev/null
   ```

3. **Download if missing:**
   ```bash
   curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
   ```

### If File Size is Wrong:

- **Too small (< 7 MB)**: Download incomplete, re-download
- **Too large (> 8 MB)**: Wrong file, delete and re-download
- **Correct size (7.0-8.0 MB)**: File is correct ✓

---

## 📝 Summary Commands

### One-Line Check:

```bash
[ -f "hand_landmarker.task" ] && echo "✓ Model exists ($(ls -lh hand_landmarker.task | awk '{print $5}'))" || echo "✗ Model not found"
```

### Detailed Check:

```bash
python3 << 'EOF'
import os
path = "hand_landmarker.task"
if os.path.exists(path):
    size = os.path.getsize(path) / (1024 * 1024)
    print(f"✓ Model found: {os.path.abspath(path)}")
    print(f"  Size: {size:.2f} MB")
    print(f"  Status: {'✓ Valid' if 7.0 <= size <= 8.0 else '⚠ Check size'}")
else:
    print("✗ Model not found")
    print("  Download: curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
EOF
```

---

**For your MacBook, use these commands to verify the AI model is installed!** 🍎
