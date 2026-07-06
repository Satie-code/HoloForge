# Walkthrough

This walkthrough guides you through creating a small glowing structure, exploring camera orbit, effects, materials, and scene save/load.

## 1) Start the App

- Normal mode:
  - `python holoforge/main.py`
- Confirm you see the camera background, grid, and a status bar.

## 2) Enable Bloom and Emissive

- Open the radial menu and choose “Toggle Bloom” (or press B).
- Choose “Toggle Emissive” (or press E).
- The status bar updates and HUD briefly confirms.

## 3) Pick a Material and Color

- Cycle Material to “Glass” (or press M until Glass shows).
- Change Voxel Color to a brighter color (or press C to cycle).

## 4) Place Voxels

- Single placement:
  - Move your fingertip to a grid cell; the ghost cube marks the position.
  - Confirm your placement gesture; the voxel commits.
- Continuous build:
  - Toggle “Continuous Build” On (radial menu or N).
  - Slowly move across grid cells; positions interpolate to the build buffer.
  - Commit the buffer to add all voxels.

## 5) Orbit and Inspect

- Use your input mapping to enter orbit mode.
- The camera orbits around the voxel grid centroid.
- Reset view via the orbit reset action when needed.

## 6) Delete and Clear

- To remove the current voxel under the cursor, use your configured gesture mapping for deletion.
- Clear Scene via radial menu (or K) if you want to restart.

## 7) Save and Load

- Save Scene (radial or S) — writes `holoforge_scene.json`.
- Load Scene (radial or L) — restores voxels, defaults, and toggles.
- Verify that color, emissive/material defaults, and bloom/grid toggles match the saved state.

## 8) Tips

- For stronger glow, increase Bloom Strength and lower Threshold in `holoforge/core/config.py`.
- For performance with large builds, instanced rendering keeps GPU usage efficient.
- Safe mode:
  - `set HOLOFORGE_SAFE_MODE=1`
  - `python holoforge/main.py`
  - Useful for debugging camera and basic overlays.
