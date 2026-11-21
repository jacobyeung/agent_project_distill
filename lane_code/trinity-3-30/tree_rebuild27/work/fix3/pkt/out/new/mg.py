"""Answer the device queries of the numeric library without the driver while the device mask is empty."""
import os
from contextlib import contextmanager


def masked():
    return os.environ.get('CUDA_VISIBLE_DEVICES') == ''


@contextmanager
def guard():
    """A driver query made under an empty mask leaves the process unable to open a device after the
    mask is lifted. Inside this block, while the mask is empty, is_available() is False,
    device_count() is 0 and _lazy_init() raises the library's own error; none of them calls the
    driver. Under any other mask the originals answer, and the originals are put back on exit."""
    import torch
    cuda = torch.cuda
    native = (cuda.is_available, cuda.device_count, cuda._lazy_init)

    def is_available():
        return False if masked() else native[0]()

    def device_count():
        return 0 if masked() else native[1]()

    def _lazy_init():
        if masked():
            raise RuntimeError('No CUDA GPUs are available')
        return native[2]()

    cuda.is_available, cuda.device_count, cuda._lazy_init = is_available, device_count, _lazy_init
    try:
        yield
    finally:
        cuda.is_available, cuda.device_count, cuda._lazy_init = native
