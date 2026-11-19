"""GT geometry conventions for head-call values, and the unprojection the student applies to its responses.

The reference frame is rung-1's (build_rung1.Geometry) and phase 1's gravity reference: anchored at the camera of
input frame 1, x right, y forward (the horizontal projection of that camera's optical axis), z up (gravity), metres.
Camera poses are the 32 metric OpenCV camera-to-world matrices of the scene, index k-1 for frame k. Pixels on the
240x320 first-hit raster map to the [0, 1000] grid at pixel centres ((c + 0.5) / W * 1000), the same mapping as
phase 1's label bank and its depth head's grid_sample (align_corners=False).

A pose is (position, heading, pitch, roll, view): heading is the optical axis's yaw from +y (left positive), pitch
its elevation, roll the rotation about it (left = counterclockwise seen from behind, the camera's right side
raised), view the horizontal and vertical field of view. rotation_from_angles rebuilds the camera-to-reference
rotation from those angles, and unproject turns a depth response at a grid point into a reference-frame point with
phase 1's pinhole convention (principal point at the image centre, gate_eval.unproject).

Principal point and rounding (deliberate). The pose head predicts a field of view and no principal point (phase 1's
camera encoding [t, q, fov_h, fov_w]), and a response prints angles and the view in whole degrees, so the student
can only unproject with a centred principal point and the printed values; the GT responses follow the same rule so
that every derived number is reproducible from the trace. Measured on the 1,383 metric rows of 72 bank items that
reach a derivation (convert_rung1 --exact-diagnostic): of 299 rows whose printed derivation misses the GT answer, 4 would agree with
full-precision points and the calibrated principal point, and 6 agreeing rows would flip the other way. The
disagreements come from deriving from one visible surface pixel per object while the GT answer uses the OBB centre
(directions) or the closest box points (distances); those rows take the answer-only fallback. validate_geometry
bounds the derived point against the exact calibrated surface point (p99 <= 0.10 m).
"""
import math

from .protocol import GRID, PoseValue

RASTER_HW = (240, 320)
UP = (0.0, 0.0, 1.0)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(v):
    norm = math.sqrt(_dot(v, v))
    return tuple(x / norm for x in v)


def angles_of_rotation(columns):
    """(heading, pitch, roll) in degrees of a camera-to-reference rotation given as its columns (x, y, z axes of the
    OpenCV camera in reference coordinates, z up)."""
    x_axis, y_axis, forward = (_unit(c) for c in columns)
    heading = math.degrees(math.atan2(-forward[0], forward[1]))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, forward[2]))))
    roll = math.degrees(math.atan2(x_axis[2], -y_axis[2]))
    return heading, pitch, roll


def rotation_from_angles(heading_deg, pitch_deg, roll_deg=0.0):
    """Camera-to-reference rotation (rows of a 3x3 matrix) with these heading, pitch and roll."""
    h, p, r = (math.radians(float(v)) for v in (heading_deg, pitch_deg, roll_deg))
    forward = (-math.sin(h) * math.cos(p), math.cos(h) * math.cos(p), math.sin(p))
    right0 = (math.cos(h), math.sin(h), 0.0)
    down0 = _cross(forward, right0)
    x_axis = tuple(math.cos(r) * a - math.sin(r) * b for a, b in zip(right0, down0))
    y_axis = tuple(math.sin(r) * a + math.cos(r) * b for a, b in zip(right0, down0))
    return tuple(tuple(col[i] for col in (x_axis, y_axis, forward)) for i in range(3))


def view_of_intrinsics(intrinsics, calibration_hw):
    """(horizontal, vertical) field of view in degrees (phase 1's fov_w, fov_h: 2 atan(W / 2 fx), 2 atan(H / 2 fy))."""
    height, width = calibration_hw
    fx, fy = float(intrinsics[0][0]), float(intrinsics[1][1])
    return (math.degrees(2.0 * math.atan(width / (2.0 * fx))), math.degrees(2.0 * math.atan(height / (2.0 * fy))))


def unproject(point, depth, pose):
    """Reference-frame point of grid point [x, y] at optical-axis depth `depth` seen from `pose` (PoseValue with view).

    This is the derivation the trace text states after a depth call: it uses only the call's point and the values
    the pose and depth responses print."""
    if pose.view_deg is None:
        raise ValueError("unprojection needs the frame's field of view")
    fov_w, fov_h = (math.radians(float(v)) for v in pose.view_deg)
    d = float(depth)
    camera = ((float(point[0]) / (GRID / 2.0) - 1.0) * math.tan(fov_w / 2.0) * d,
              (float(point[1]) / (GRID / 2.0) - 1.0) * math.tan(fov_h / 2.0) * d, d)
    rot = rotation_from_angles(pose.heading_deg, pose.pitch_deg, pose.roll_deg)
    return tuple(float(pose.position[i]) + sum(rot[i][j] * camera[j] for j in range(3)) for i in range(3))


class Reference(object):
    """Frame-1 gravity-aligned reference over a scene's 32 camera-to-world poses.

    `up` is the gravity direction in the poses' world frame ((0, 0, 1) for the scene snapshots). `intrinsics` (32
    3x3 matrices of the calibration raster `calibration_hw`) give each frame's view; without them a pose has no view.
    Frame 1's pose has no view either: phase 1's pose head predicts none for the origin."""

    def __init__(self, poses, up=UP, intrinsics=None, calibration_hw=None):
        if len(poses) != 32 or poses[0] is None:
            raise ValueError("Expected the 32 input-frame camera poses, frame 1 included")
        self.poses = poses
        self.intrinsics, self.calibration_hw = intrinsics, calibration_hw
        self.up = _unit(up)
        self.origin = self.position_world(1)
        forward = self.forward_world(1)
        horizontal = tuple(f - _dot(forward, self.up) * u for f, u in zip(forward, self.up))
        if sum(v * v for v in horizontal) ** 0.5 < 1e-6:
            raise ValueError("Frame 1 looks along gravity: its horizontal forward is undefined")
        self.y = _unit(horizontal)
        self.x = _cross(self.y, self.up)
        self.z = self.up

    def position_world(self, frame):
        pose = self.poses[frame - 1]
        return (pose[0][3], pose[1][3], pose[2][3])

    def axis_world(self, frame, column):
        pose = self.poses[frame - 1]
        return (pose[0][column], pose[1][column], pose[2][column])

    def forward_world(self, frame):
        return self.axis_world(frame, 2)  # camera +z (OpenCV) in world coordinates

    def local(self, point):
        d = tuple(p - o for p, o in zip(point, self.origin))
        return (_dot(d, self.x), _dot(d, self.y), _dot(d, self.z))

    def local_direction(self, vector):
        return (_dot(vector, self.x), _dot(vector, self.y), _dot(vector, self.z))

    def angles(self, frame):
        return angles_of_rotation([self.local_direction(self.axis_world(frame, c)) for c in range(3)])

    def heading(self, frame):
        return self.angles(frame)[0]

    def pitch(self, frame):
        return self.angles(frame)[1]

    def view(self, frame):
        if self.intrinsics is None or frame == 1:
            return None
        return view_of_intrinsics(self.intrinsics[frame - 1], self.calibration_hw)

    def pose(self, frame):
        heading, pitch, roll = self.angles(frame)
        return PoseValue(self.local(self.position_world(frame)), heading, pitch, roll, self.view(frame))

    def camera_point(self, frame, point_local):
        """A reference-frame point in frame's OpenCV camera coordinates."""
        world = tuple(o + point_local[0] * a + point_local[1] * b + point_local[2] * c
                      for o, a, b, c in zip(self.origin, self.x, self.y, self.z))
        pose = self.poses[frame - 1]
        d = tuple(w - pose[i][3] for i, w in enumerate(world))
        return tuple(sum(pose[r][c] * d[r] for r in range(3)) for c in range(3))


def raster_to_grid(xr, yr, raster_hw=RASTER_HW):
    """Raster pixel (column, row) of the first-hit raster -> [x, y] on the [0, 1000] grid at the pixel centre."""
    height, width = raster_hw
    x = int(round((float(xr) + 0.5) / float(width) * GRID))
    y = int(round((float(yr) + 0.5) / float(height) * GRID))
    return max(0, min(GRID, x)), max(0, min(GRID, y))


def grid_to_raster(point, raster_hw=RASTER_HW):
    """[x, y] grid point -> (row, column) of the raster pixel that contains it."""
    height, width = raster_hw
    column = min(width - 1, int(math.floor(point[0] / float(GRID) * width)))
    row = min(height - 1, int(math.floor(point[1] / float(GRID) * height)))
    return row, column


def backproject(point, depth, intrinsics, pose, calibration_hw):
    """World point of a grid pixel at the given optical-axis depth (intrinsics in the calibration raster)."""
    height, width = calibration_hw
    u = point[0] / float(GRID) * width
    v = point[1] / float(GRID) * height
    fx, fy, cx, cy = intrinsics[0][0], intrinsics[1][1], intrinsics[0][2], intrinsics[1][2]
    camera = ((u - cx) * depth / fx, (v - cy) * depth / fy, depth)
    return tuple(sum(pose[r][c] * camera[c] for c in range(3)) + pose[r][3] for r in range(3))


def box_distance(point, centroid, axes, lengths):
    """Distance from a point to an oriented box (0 inside); axes are three unit rows, lengths full edge lengths."""
    d = [p - c for p, c in zip(point, centroid)]
    outside = 0.0
    for axis, length in zip(axes, lengths):
        excess = abs(_dot(d, axis)) - length / 2.0
        if excess > 0:
            outside += excess * excess
    return math.sqrt(outside)


def pose_from_gravity_rt(rot, trans, fov_hw_rad=None):
    """PoseValue of phase 1's head_api pose: R [3, 3] camera-to-gravity-reference, t [3] the camera centre (metres),
    fov_hw_rad (vertical, horizontal) radians from info['fov_hw_rad'] (None for the origin frame). The head has no
    principal point to pass on, and the response prints whole degrees: see the module docstring."""
    r = [[float(rot[i][j]) for j in range(3)] for i in range(3)]
    columns = [(r[0][c], r[1][c], r[2][c]) for c in range(3)]
    heading, pitch, roll = angles_of_rotation(columns)
    view = None
    if fov_hw_rad is not None:
        view = (math.degrees(float(fov_hw_rad[1])), math.degrees(float(fov_hw_rad[0])))
    return PoseValue((float(trans[0]), float(trans[1]), float(trans[2])), heading, pitch, roll, view)


def rotation_error_deg(a, b):
    """Geodesic angle between the camera rotations of two PoseValues (heading, pitch and roll)."""
    ra, rb = rotation_from_angles(a.heading_deg, a.pitch_deg, a.roll_deg), rotation_from_angles(
        b.heading_deg, b.pitch_deg, b.roll_deg)
    trace = sum(ra[k][i] * rb[k][i] for i in range(3) for k in range(3))
    return math.degrees(math.acos(max(-1.0, min(1.0, 0.5 * (trace - 1.0)))))
