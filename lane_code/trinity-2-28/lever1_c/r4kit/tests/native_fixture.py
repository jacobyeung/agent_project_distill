"""Local Python torchvision fixture; never installs or executes CUDA kernels."""
from pathlib import Path
import shutil


def prepare(root):
    site = root/'tmp/native_site'
    target = site/'torchvision'
    if not target.exists():
        site.mkdir(parents=True, exist_ok=True)
        source = Path('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages/torchvision')
        shutil.copytree(source, target)
    return site
