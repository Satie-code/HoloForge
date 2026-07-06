# Setup Guide

## 1) Prerequisites

- Windows 10+ (x64)
- Python 3.10+
- OpenGL 3.3-capable GPU with current drivers
- Webcam (720p+ recommended)

## 2) Create a Virtual Environment

```bash
cd c:\Material\Repo\HoloForge
python -m venv .venv
.venv\Scripts\activate
```

## 3) Install Dependencies

```bash
pip install moderngl moderngl-window numpy pyrr opencv-python mediapipe
```

## 4) First Run

```bash
python holoforge/main.py
```

- Normal mode launches the full pipeline: camera → 3D scene → optional bloom → screen.

## 5) Safe Mode (Optional)

```bash
set HOLOFORGE_SAFE_MODE=1
python holoforge/main.py
```

- Shows a simple cv2 window with camera and a 2D preview square.
- Useful if OpenGL context creation fails or for quick camera checks.

## 6) Configuration

- Edit `holoforge/core/config.py`:
  - WINDOW_WIDTH, WINDOW_HEIGHT
  - VOXEL_SIZE
  - GRID_COLOR
  - VOXEL_DEFAULT_COLOR
  - VOXEL_PREVIEW_ALPHA
  - ORBIT_DEFAULT_RADIUS, ORBIT_SMOOTH_FACTOR, ORBIT_SENSITIVITY
  - DEFAULT_EMISSIVE
  - DEFAULT_MATERIAL_METALLIC, DEFAULT_MATERIAL_ROUGHNESS
  - BLOOM_ENABLED, BLOOM_THRESHOLD, BLOOM_STRENGTH, BLOOM_BLUR_PASSES

## 7) Using the App

- Radial menu:
  - Open: left wrist circle while pinched
  - Select: aim with right index fingertip
  - Confirm: right pinch release
  - Close: left palm close
- Keyboard shortcuts (dev):
  - S: Save Scene
  - L: Load Scene
  - B: Toggle Bloom
  - G: Toggle Grid Visibility
  - C: Change Voxel Color
  - M: Cycle Material
  - E: Toggle Emissive
  - N: Toggle Continuous Build
  - K: Clear Scene

## 8) Save/Load Scenes

- Save writes `holoforge_scene.json` in repo root
- Load restores voxels and runtime defaults/toggles

## 9) Troubleshooting

- If the window fails to start:
  - Update GPU drivers and ensure OpenGL 3.3 support
  - Try Safe Mode
  - Ensure the virtual environment is active and dependencies are installed
- Camera not detected:
  - Verify webcam access permissions
  - Close other apps using the camera
- Performance:
  - Instancing is enabled; large scenes should remain responsive
  - Reduce bloom passes or resolution if needed
