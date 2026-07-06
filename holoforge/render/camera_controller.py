import numpy as np
from pyrr import Matrix44, Vector3


class CameraController:
    def __init__(self, radius: float = 5.0, smooth: float = 0.1, sensitivity: float = 2.0):
        self.radius = radius
        self.smooth = smooth
        self.sensitivity = sensitivity
        self.theta = 0.0
        self.phi = 0.0
        self.target_theta = 0.0
        self.target_phi = 0.0
        self.center = Vector3([0.0, 0.0, 0.0])

    def set_center(self, center):
        self.center = Vector3(center)

    def reset(self):
        self.theta = 0.0
        self.phi = 0.0
        self.target_theta = 0.0
        self.target_phi = 0.0

    def apply_delta(self, delta_xy):
        dx, dy = delta_xy
        self.target_theta += dx * self.sensitivity
        self.target_phi += dy * self.sensitivity
        self.target_phi = np.clip(self.target_phi, -np.pi * 0.49, np.pi * 0.49)

    def update(self):
        self.theta += (self.target_theta - self.theta) * self.smooth
        self.phi += (self.target_phi - self.phi) * self.smooth

    def view_matrix(self) -> Matrix44:
        x = self.center.x + self.radius * np.cos(self.phi) * np.cos(self.theta)
        y = self.center.y + self.radius * np.sin(self.phi)
        z = self.center.z + self.radius * np.cos(self.phi) * np.sin(self.theta)
        eye = Vector3([x, y, z])
        up = Vector3([0.0, 1.0, 0.0])
        return Matrix44.look_at(eye, self.center, up)
