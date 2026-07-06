# HoloForge Requirements

## System Requirements

- Operating system: Windows 10 or later (x64)
- GPU: OpenGL 3.3 capable graphics card and up-to-date drivers
- CPU: Modern x64 processor; AVX recommended for best performance
- RAM: 4 GB minimum; 8 GB recommended
- Camera: 720p or 1080p RGB webcam for hand tracking
- Disk: ~200 MB free space for dependencies and cache

## Software Requirements

- Python: 3.10 or newer
- Pip and virtual environment utilities

## Python Dependencies

- moderngl
- moderngl-window
- numpy
- pyrr
- opencv-python
- mediapipe

Install them with:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install moderngl moderngl-window numpy pyrr opencv-python mediapipe
```

## Optional/Advanced

- Visual C++ Redistributable (Windows) if required by binary wheels
- GPU supporting floating point textures for bloom performance
- External lighting or consistent background for reliable hand tracking

## Runtime Requirements Summary

- OpenGL 3.3 context creation through moderngl-window
- Webcam access through OpenCV
- File system write permission to save holoforge_scene.json
