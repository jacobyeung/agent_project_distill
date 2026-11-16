"""Gated tar reader (Python 3.6, stdlib): writes a tar stream of the listed files to stdout, keeping their full paths
without the leading '/'. It stops itself (SIGSTOP) after reading the list and before opening any source file, so the
lane can register its unchanged identity with the IO governor and then resume it.
usage: tar_reader.py LIST PIDFILE | pv ... | tar xf - -C DEST
"""
import os
import signal
import sys
import tarfile


def main():
    paths = [line.rstrip("\n") for line in open(sys.argv[1]) if line.strip()]
    with open(sys.argv[2] + ".part", "w") as stream:
        stream.write(str(os.getpid()))
    os.rename(sys.argv[2] + ".part", sys.argv[2])
    os.kill(os.getpid(), signal.SIGSTOP)
    missing = 0
    with tarfile.open(fileobj=sys.stdout.buffer, mode="w|", format=tarfile.GNU_FORMAT) as archive:
        for path in paths:
            try:
                archive.add(path, arcname=path.lstrip("/"), recursive=False)
            except OSError as error:
                missing += 1
                sys.stderr.write("tar_reader: %s\n" % error)
    sys.stderr.write("tar_reader: %d files, %d unreadable\n" % (len(paths), missing))
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
