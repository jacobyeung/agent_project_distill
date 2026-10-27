"""Copy stdin to stdout at a capped byte rate, pausing while the shared Trinity IO meter reads above a threshold.

usage: tar cf - ... | python3 throttle.py RATE_BYTES_PER_S PAUSE_MB_PER_S | tar xf -
The meter is the TOTAL row of the first 20 lines of IO_USAGE.md, column "Read + 2x write" (MB/s). Python 3.6 compatible.
"""
import sys
import time

METER = "/data3/jjyeung/orch_n13_20261026/io_meter/IO_USAGE.md"


def meter_total():
    try:
        with open(METER) as stream:
            for number, line in enumerate(stream):
                if number >= 20:
                    break
                if line.startswith("| TOTAL"):
                    return float(line.split("|")[4].strip())
    except (OSError, ValueError, IndexError):
        return None
    return None


def main():
    rate, pause = float(sys.argv[1]), float(sys.argv[2])
    chunk = 64 * 1024
    source, sink = sys.stdin.buffer, sys.stdout.buffer
    start, sent, checked = time.time(), 0, 0.0
    while True:
        now = time.time()
        if now - checked > 60:
            checked = now
            while True:
                total = meter_total()
                if total is None or total <= pause:
                    break
                sys.stderr.write("%s pause meter=%.2f\n" % (time.strftime("%H:%M:%S"), total))
                sys.stderr.flush()
                time.sleep(60)
            start, sent = time.time(), 0
        data = source.read(chunk)
        if not data:
            break
        sink.write(data)
        sent += len(data)
        ahead = sent / rate - (time.time() - start)
        if ahead > 0:
            time.sleep(ahead)
    sink.flush()


if __name__ == "__main__":
    main()
