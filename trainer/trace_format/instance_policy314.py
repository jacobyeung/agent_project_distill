"""Shared v3.14 instance admission; pixels are measured at the reference raster."""
import math
min_mask_px = 154  # prog_v2.MIN_PX -> programs.MIN_PX, 320 x 240.
def mask_floor(shape):
    return max(1, math.ceil(min_mask_px * int(shape[-2]) * int(shape[-1]) / (320 * 240)))
def valid_mask(mask):
    return int(mask.sum()) >= mask_floor(mask.shape)
