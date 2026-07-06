# How To Use This App

## Launch

- Normal mode:
  - `python holoforge/main.py`
- Safe mode (debug overlay and camera-only window):
  - `set HOLOFORGE_SAFE_MODE=1`
  - `python holoforge/main.py`

## What You See

- Camera background composited under the 3D scene
- Holographic grid (toggle visibility)
- Committed voxels rendered via GPU instancing
- Ghost preview cube at the current grid position
- Build buffer preview path (when placing multiple voxels)
- Delete highlight cube for the next deletion
- Bloom post-processing (optional)
- Status bar and short HUD messages

## Building Voxels

- Single placement
  - Move your fingertip to the desired grid cell; a ghost cube appears
  - Confirm placement using your configured gesture mapping
- Continuous build
  - Toggle “Continuous Build” On
  - Move across cells; the app interpolates positions and queues them in the build buffer
  - Commit the build buffer to add voxels

## Radial Menu

- Open: left wrist circle while pinched
- Select: point with right index finger near a wedge
- Confirm: right pinch release
- Close: left palm close
- Options:
  - Toggle Continuous Build
  - Change Voxel Color
  - Clear Scene
  - Toggle Grid Visibility
  - Toggle Bloom
  - Toggle Emissive
  - Cycle Material (Matte, Metal, Glass)
  - Save Scene
  - Load Scene

## Keyboard Shortcuts (Dev)

- S: Save Scene
- L: Load Scene
- B: Toggle Bloom
- G: Toggle Grid Visibility
- C: Change Voxel Color
- M: Cycle Material
- E: Toggle Emissive
- N: Toggle Continuous Build
- K: Clear Scene

## Save/Load Scenes

- Save writes `holoforge_scene.json` to the repo root
- Load restores voxels, color defaults, material defaults, and toggles (continuous build, grid, bloom)

## Visual Effects

- Bloom:
  - Enable via menu or shortcut
  - Strength/threshold/passes configurable in `holoforge/core/config.py`
- Emissive:
  - Per-voxel flag; increases glow contribution and highlight

## Materials

- Each voxel has metallic and roughness
- Presets in the radial menu apply to future voxels
- Existing voxels retain their material values

## Status and HUD

- Status bar shows: CB/Grid/Bloom, current color, emissive, material
- HUD messages appear for ~2 seconds after actions (e.g., “Bloom: On”)
