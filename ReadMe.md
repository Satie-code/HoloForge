# HoloForge

## Overview

- Hand-tracked voxel builder that composites a live camera feed under a 3D scene
- Ghost cube preview for precise placement, plus continuous build with interpolation
- GPU instancing for performance at large voxel counts
- Bloom post-processing with configurable strength, threshold, and blur passes
- Materials with metallic and roughness; emissive for glow contribution
- Radial menu for natural gesture-driven controls
- Status bar and short HUD messages for immediate feedback
- Scene Save/Load to JSON (voxels + defaults + toggles)

## Requirements

- Windows 10+ (x64), Python 3.10+, OpenGL 3.3-capable GPU, webcam
- See detailed requirements: [Requirement.md](file:///c:/Material/Repo/HoloForge/Requirement.md)

## Quick Start

- Create venv and install dependencies:
  - `python -m venv .venv`
  - `.venv\Scripts\activate`
  - `pip install moderngl moderngl-window numpy pyrr opencv-python`
- Run:
  - `python holoforge/main.py` (or `python -m holoforge.main`)
  - If the OpenGL window fails to initialize (e.g. pyglet error), the app will
    automatically fall back to "safe mode" in which only the camera preview is
    shown and gesture handling still works.
- Safe Mode (force):
  - `set HOLOFORGE_SAFE_MODE=1`
  - `python holoforge/main.py`
  - Safe mode is also entered automatically when the window backend isn't
    available.

⚠️ **Note:** Ensure a compatible window backend is installed.  On Windows
`pip install pyglet==1.5.11` typically provides the `canvas` API required by
`moderngl-window`.

## Controls

- Radial Menu (gestures):
  - Toggle Continuous Build, Change Voxel Color, Clear Scene
  - Toggle Grid Visibility, Toggle Bloom
  - Toggle Emissive, Cycle Material (Matte/Metal/Glass)
  - Save Scene, Load Scene
- Keyboard (dev):
  - S/L: Save/Load Scene
  - B/G: Bloom/Grid toggle
  - C/M: Color/Material cycle
  - E/N/K: Emissive/Continuous Build/Clear Scene
- Status/HUD:
  - Status bar shows CB/Grid/Bloom, color, emissive, material
  - HUD messages appear ~2 seconds after actions

## Save/Load

- Writes and restores `holoforge_scene.json` at repo root
- Includes voxels (position, color, emissive, metallic, roughness), defaults, and toggles
- Implementation: [scene_io.py](file:///c:/Material/Repo/HoloForge/holoforge/scene/scene_io.py)

## Configuration

- Edit: [config.py](file:///c:/Material/Repo/HoloForge/holoforge/core/config.py)
- Key fields:
  - WINDOW_WIDTH/HEIGHT, VOXEL_SIZE, GRID_COLOR
  - VOXEL_DEFAULT_COLOR, VOXEL_PREVIEW_ALPHA
  - ORBIT_DEFAULT_RADIUS/SMOOTH_FACTOR/SENSITIVITY
  - DEFAULT_EMISSIVE, DEFAULT_MATERIAL_METALLIC, DEFAULT_MATERIAL_ROUGHNESS
  - BLOOM_ENABLED, BLOOM_THRESHOLD, BLOOM_STRENGTH, BLOOM_BLUR_PASSES

## Architecture

- App orchestration: [app.py](file:///c:/Material/Repo/HoloForge/holoforge/core/app.py)
- Renderer and effects: [renderer.py](file:///c:/Material/Repo/HoloForge/holoforge/render/renderer.py)
- Radial menu: [radial_menu.py](file:///c:/Material/Repo/HoloForge/holoforge/ui/radial_menu.py)
- Voxel grid + objects: [voxel_grid.py](file:///c:/Material/Repo/HoloForge/holoforge/voxel/voxel_grid.py), [voxel_object.py](file:///c:/Material/Repo/HoloForge/holoforge/voxel/voxel_object.py)
- Shaders (camera, bloom, voxel): [render/shaders](file:///c:/Material/Repo/HoloForge/holoforge/render/shaders)
- Camera capture: [vision/camera.py](file:///c:/Material/Repo/HoloForge/holoforge/vision/camera.py)

## Documentation

- Getting started: [Setup_Guide.md](file:///c:/Material/Repo/HoloForge/Setup_Guide.md)
- App usage: [How_To_Use_this_App.md](file:///c:/Material/Repo/HoloForge/How_To_Use_this_App.md)
- Scenario walkthrough: [Walkthrough.md](file:///c:/Material/Repo/HoloForge/Walkthrough.md)
- Requirements: [Requirement.md](file:///c:/Material/Repo/HoloForge/Requirement.md)
