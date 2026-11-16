import ctypes; ctypes.CDLL(None).prctl(41, 1, 0, 0, 0)
import numpy as np, json, glob, os
from PIL import Image
from scipy.spatial.transform import Rotation

def ts(s): return float(os.path.basename(s).split('_')[1].rsplit('.', 1)[0])

def load_traj(p):
    rows = np.loadtxt(p)
    return rows[:, 0], rows[:, 1:4], rows[:, 4:7]

def c2w_of(aa, t, how):
    if how == 'scipy':
        R = Rotation.from_rotvec(aa).as_matrix()
    else:
        th = np.linalg.norm(aa); k = aa / th; Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        R = np.eye(3) + np.sin(th) * Kx + (1 - np.cos(th)) * Kx @ Kx
    w2c = np.eye(4); w2c[:3, :3] = R; w2c[:3, 3] = t
    return np.linalg.inv(w2c)
