"""k6 wa.py's decode rule, verbatim: inflate (method 8), cv2.imdecode COLOR, orient (rot, then 2.5x INTER_CUBIC), PNG compression 3."""
import struct, zlib
import numpy as np
import cv2

cv2.setNumThreads(1)
SCALE = 2.5


def orient(img, rot):
    if rot == "cw":
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rot == "ccw":
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rot == "180":
        img = cv2.rotate(img, cv2.ROTATE_180)
    h, w = img.shape[:2]
    return cv2.resize(img, (int(round(w * SCALE)), int(round(h * SCALE))), interpolation=cv2.INTER_CUBIC)


def member_payload(buf, method, cs):
    """buf starts at the member's local header (wa.py: o = lho - a = 0); returns the stored PNG bytes."""
    if buf[0:4] != b"PK\x03\x04":
        raise RuntimeError("bad local header")
    n2, e2 = struct.unpack("<HH", buf[26:30])
    raw = buf[30 + n2 + e2:30 + n2 + e2 + cs]
    if len(raw) != cs:
        raise RuntimeError("short member: %d of %d" % (len(raw), cs))
    if method == 8:
        raw = zlib.decompressobj(-15).decompress(raw)
    return raw


def encode(png_bytes, rot):
    img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("decode failed")
    img2 = orient(img, rot)
    ok, enc = cv2.imencode(".png", img2, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError("imencode failed")
    return enc.tobytes(), img.shape[:2], img2.shape[:2]
