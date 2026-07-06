import os
import json
from typing import Dict, Any
from ..voxel.voxel_grid import VoxelGrid

def scene_path() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root, "holoforge_scene.json")

def save_scene(voxel_grid: VoxelGrid, shared_state: Dict[str, Any], config) -> str:
    data = {
        "voxels": [
            {
                "position": list(vox.position),
                "color": list(vox.color),
                "emissive": bool(vox.emissive),
                "metallic": float(vox.metallic),
                "roughness": float(vox.roughness),
            }
            for vox in voxel_grid.voxels.values()
        ],
        "defaults": {
            "color": list(config.VOXEL_DEFAULT_COLOR),
            "emissive": bool(voxel_grid.default_emissive),
            "metallic": float(voxel_grid.default_metallic),
            "roughness": float(voxel_grid.default_roughness),
        },
        "toggles": {
            "continuous_build": bool(config.CONTINUOUS_BUILD),
            "grid_visible": bool(shared_state.get("grid_visible", True)),
            "bloom_enabled": bool(shared_state.get("bloom_enabled", False)),
        },
    }
    path = scene_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path

def load_scene(voxel_grid: VoxelGrid, shared_state: Dict[str, Any], config) -> str:
    path = scene_path()
    if not os.path.exists(path):
        return path
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    voxel_grid.voxels.clear()
    vox_list = data.get("voxels", [])
    for v in vox_list:
        pos = tuple(v["position"])
        color = tuple(v["color"])
        emissive = bool(v.get("emissive", True))
        metallic = float(v.get("metallic", 0.0))
        roughness = float(v.get("roughness", 0.5))
        voxel_grid.add(pos, color=color, emissive=emissive, metallic=metallic, roughness=roughness)
    defaults = data.get("defaults", {})
    dc = defaults.get("color", list(config.VOXEL_DEFAULT_COLOR))
    config.VOXEL_DEFAULT_COLOR = tuple(dc)
    voxel_grid.default_emissive = bool(defaults.get("emissive", voxel_grid.default_emissive))
    voxel_grid.default_metallic = float(defaults.get("metallic", voxel_grid.default_metallic))
    voxel_grid.default_roughness = float(defaults.get("roughness", voxel_grid.default_roughness))
    toggles = data.get("toggles", {})
    config.CONTINUOUS_BUILD = bool(toggles.get("continuous_build", config.CONTINUOUS_BUILD))
    shared_state["grid_visible"] = bool(toggles.get("grid_visible", shared_state.get("grid_visible", True)))
    shared_state["bloom_enabled"] = bool(toggles.get("bloom_enabled", shared_state.get("bloom_enabled", False)))
    return path
