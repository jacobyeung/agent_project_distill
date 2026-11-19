import os
import socket
from contextlib import contextmanager
from pathlib import Path

from .io import ROOT


def validate_device(device, go_file=None):
    if device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        return
    if device != "cuda":
        raise ValueError("Use cpu or cuda with exactly one explicitly visible GPU")
    if go_file is None:
        raise PermissionError("GPU execution requires an explicit GO file in this lane's inbox")
    path = Path(go_file).resolve()
    if not path.is_relative_to((ROOT / "inbox").resolve()):
        raise PermissionError("GO approval must be inside this lane's inbox")
    if "GO" not in [line.strip() for line in path.read_text().splitlines()]:
        raise PermissionError("The approval must contain a standalone GO line")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if not visible or "," in visible or visible in ("-1", "all"):
        raise PermissionError("Exactly one GPU must be selected explicitly")


@contextmanager
def offline_model():
    previous = socket.create_connection
    def refuse(*args, **kwargs):
        raise RuntimeError("Automatic model networking is disabled; stage the approved asset serially")
    socket.create_connection = refuse
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        yield
    finally:
        socket.create_connection = previous
