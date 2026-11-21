"""Answer the device queries of the numeric library without the driver while the device mask is empty."""
import os
from contextlib import contextmanager


def masked():
    return os.environ.get('CUDA_VISIBLE_DEVICES') == ''


@contextmanager
def guard():
    """A driver query made under an empty mask by a process that has not opened a device leaves the
    process unable to open one after the mask is lifted. Inside this block, while the mask is empty
    and the library is not initialized, is_available() is False, device_count() is 0 and
    _lazy_init() raises the library's own error; none of them calls the driver. A process that
    initialized the library before the mask keeps its devices under it, so there, and under any
    other mask, the originals answer. The originals are put back on exit."""
    import torch
    cuda = torch.cuda
    native = (cuda.is_available, cuda.device_count, cuda._lazy_init)

    def answering():
        return masked() and not cuda.is_initialized()

    def is_available():
        return False if answering() else native[0]()

    def device_count():
        return 0 if answering() else native[1]()

    def _lazy_init():
        if answering():
            raise RuntimeError('No CUDA GPUs are available')
        return native[2]()

    cuda.is_available, cuda.device_count, cuda._lazy_init = is_available, device_count, _lazy_init
    try:
        yield
    finally:
        cuda.is_available, cuda.device_count, cuda._lazy_init = native
