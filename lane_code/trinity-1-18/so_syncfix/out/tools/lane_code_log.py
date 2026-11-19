# lane_code_log.py <log> <stdin-file|-> <append:0|1> <command...>
# Linux: bounded regular descriptors for a command whose own timeout owns its lifetime.
import ctypes
import fcntl
import os
import subprocess
import sys

LIMIT = 65536


def sealed_log():
    # Python 3.6 lacks os.memfd_create; glibc 2.27+ exposes the same Linux call.
    if hasattr(os, 'memfd_create'):
        fd = os.memfd_create('lane-code-log', 3)  # CLOEXEC | ALLOW_SEALING
    else:
        libc = ctypes.CDLL(None, use_errno=True)
        create = libc.memfd_create
        create.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        create.restype = ctypes.c_int
        fd = create(b'lane-code-log', 3)
        if fd < 0:
            number = ctypes.get_errno()
            raise OSError(number, os.strerror(number))
    try:
        # Populate by writes, without any file-deletion or truncation operation.
        remaining = LIMIT
        while remaining:
            remaining -= os.write(fd, b'\0' * remaining)
        os.lseek(fd, 0, os.SEEK_SET)
        # These Linux ABI values predate all supported cluster kernels.
        fcntl.fcntl(fd, 1033, 7)  # F_ADD_SEALS: SEAL_SEAL | SEAL_SHRINK | SEAL_GROW
        return fd
    except BaseException:
        os.close(fd)
        raise


def main():
    path, input_path, append = sys.argv[1:4]
    fd = sealed_log()
    try:
        if append == '1':
            with open(path, 'rb') as previous:
                os.write(fd, previous.read(LIMIT))
        with open('/dev/null' if input_path == '-' else input_path, 'rb') as source:
            # Do not read a pipe or wait for EOF. A master may retain this regular fd;
            # the kernel enforces its size, and the foreground timeout still returns.
            rc = subprocess.call(sys.argv[4:], stdin=source, stdout=fd, stderr=fd, close_fds=True)
        snapshot = os.pread(fd, LIMIT, 0).rstrip(b'\0')
        with open(path, 'wb') as target:
            target.write(snapshot)
        return rc if rc >= 0 else 128 - rc
    finally:
        os.close(fd)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('bounded log failed: %s' % error, file=sys.stderr)
        sys.exit(70)
