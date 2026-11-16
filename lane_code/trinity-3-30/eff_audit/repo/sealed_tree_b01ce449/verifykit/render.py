"""Deterministic native-mask crops; outlines have width two at output resolution."""
import hashlib
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

VARIANTS = ('outline', 'plain', 'dim')


def crop_box(mask):
    mask = np.asarray(mask, bool)
    if mask.shape != (480, 640) or not mask.any():
        raise ValueError('Expected a nonempty native 480x640 mask')
    yy, xx = np.nonzero(mask)
    x0, y0, x1, y1 = xx.min(), yy.min(), xx.max()+1, yy.max()+1
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w, h = max(160, (x1-x0)*1.6), max(160, (y1-y0)*1.6)
    return (max(0, math.floor(cx-w/2)), max(0, math.floor(cy-h/2)),
            min(640, math.ceil(cx+w/2)), min(480, math.ceil(cy+h/2)))


def render(image, mask, variant='outline'):
    if variant not in VARIANTS:
        raise ValueError(variant)
    image = image.convert('RGB')
    if image.size != (640, 480):
        raise ValueError('Expected native RGB 640x480')
    box = crop_box(mask)
    crop = image.crop(box)
    scale = 448/max(crop.size)
    size = tuple(max(1, int(math.floor(x*scale+.5))) for x in crop.size)
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    m = Image.fromarray(np.asarray(mask, bool)).crop(box).resize(size, Image.Resampling.NEAREST)
    arr, m = np.array(crop), np.asarray(m, bool)
    if variant == 'dim':
        arr[~m] = np.floor(arr[~m].astype(float)*.4+.5).astype(np.uint8)
    elif variant == 'outline':
        edge = m & ~ndimage.binary_erosion(m, structure=np.ones((3, 3)), iterations=2, border_value=0)
        arr[edge] = [255, 0, 0]
    out = Image.new('RGB', (448, 448), (128, 128, 128))
    offset = ((448-size[0])//2, (448-size[1])//2)
    out.paste(Image.fromarray(arr), offset)
    meta = dict(box=list(box), resized=list(size), offset=list(offset), variant=variant,
                rgb_sha256=hashlib.sha256(out.tobytes()).hexdigest())
    return out, meta


# Fixed bitmap digits avoid system-font variation in the numbered sheet.
DIGITS = {'1':['010','110','010','010','111'], '2':['111','001','111','100','111'],
          '3':['111','001','111','001','111'], '4':['101','101','111','001','001'],
          '5':['111','100','111','001','111']}


def sheet(crops):
    if not 1 <= len(crops) <= 5:
        raise ValueError('V2 requires 1..5 candidates per sheet')
    image = Image.new('RGB', (1344, 896), (128, 128, 128))
    draw = ImageDraw.Draw(image)
    for i, crop in enumerate(crops):
        x, y = i%3*448, i//3*448
        image.paste(crop, (x, y))
        draw.rectangle((x+6, y+6, x+46, y+54), fill='white')
        for r, row in enumerate(DIGITS[str(i+1)]):
            for c, bit in enumerate(row):
                if bit == '1':
                    draw.rectangle((x+14+c*8, y+10+r*8, x+21+c*8, y+17+r*8), fill='black')
    return image


def prompt(form, name, variant='outline'):
    if form == 'V1':
        subject = {'outline': 'object outlined in red', 'plain': 'object in the center',
                   'dim': 'undimmed object'}[variant]
        return f'Is the {subject} a {name}? Answer yes or no.'
    if form == 'V2':
        return f'Which numbered object is the {name}? Answer with one number, or 0 if none.'
    if form == 'V3':
        return f'Locate the {name}. Output JSON [{{"bbox_2d": [x1, y1, x2, y2], "label": "{name}"}}] or [].'
    raise ValueError(form)
