"""Explicit CPU entry for existing native admission, with separate telemetry.

This entry produces the existing path-bound native journal. It does not publish
a portable store and must not be described as cross-run adoption.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import resource
import signal
import time
import uuid


def resources(threads, memory_gib, max_seconds):
    if os.environ.get("TK_NATIVE_CPU_PREPARE") != "1":
        raise ValueError("TK_NATIVE_CPU_PREPARE=1 is required")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("CPU preparation requires explicitly empty CUDA_VISIBLE_DEVICES")
    for name in ("SLURM_GPUS_ON_NODE", "SLURM_GPUS", "SLURM_JOB_GPUS", "SLURM_GPUS_PER_NODE"):
        if os.environ.get(name, "") not in ("", "0"):
            raise ValueError("CPU preparation refuses a GPU allocation: " + name)
    if type(threads) is not int or not 1 <= threads <= 8:
        raise ValueError("CPU preparation supports one to eight threads")
    if type(memory_gib) is not int or not 8 <= memory_gib <= 512:
        raise ValueError("Invalid native memory ceiling")
    if type(max_seconds) is not int or not 1 <= max_seconds <= 86400:
        raise ValueError("Invalid wall limit")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[name] = str(threads)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def prepare(config, config_sha256, output, roots, *, threads=8, memory_gib=30,
            sample_size=64, max_seconds=21600, resume=False):
    resources(threads, memory_gib, max_seconds)
    if type(sample_size) is not int or sample_size < 1:
        raise ValueError("A nonempty native frame sample is required")
    # Imports follow CPU resource configuration; no GPU probe is performed.
    from .p3_provenance import file_pin
    from .s1_admission import admit
    pin = file_pin(config)
    if pin["sha256"] != config_sha256:
        raise ValueError("Input configuration differs from the explicit pin")
    output = Path(output).absolute()
    if (not any(output.is_relative_to(root) and output != root
                for root in (Path("/scratch"), Path("/tmp/jjyeung")))
            or ".." in output.parts
            or any(p.is_symlink() for p in (output, *output.parents))):
        raise ValueError("Native output must be unlinked node-local scratch")
    if resume:
        if not output.is_dir():
            raise ValueError("Native resume directory is absent")
    else:
        output.mkdir(mode=0o700, exist_ok=False)
    fd = os.open(output / "admission.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    started = time.monotonic()
    attempt = uuid.uuid4().hex
    telemetry = {"schema": "native-cpu-prepare-telemetry-v1", "attempt": attempt,
                 "config_sha256": pin["sha256"], "threads": threads, "memory_limit_gib": memory_gib,
                 "store_published": False, "cross_run_adoptable": False, "production_authorized": False}
    previous = None
    timer = None
    owns_lock = False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        owns_lock = True

        def timeout(*_):
            raise TimeoutError("Native CPU preparation exceeded its wall limit")

        previous = signal.signal(signal.SIGALRM, timeout)
        timer = signal.setitimer(signal.ITIMER_REAL, max_seconds)
        result = admit(pin, output, roots, threads=threads, memory_gib=memory_gib,
                       sample_size=sample_size, max_seconds=max_seconds,
                       attempt=attempt, prepare_only=True)
        telemetry["status"] = "PREPARED"
        telemetry["native_data_receipt_sha256"] = file_pin(output / "data_receipt.json")["sha256"]
        return result
    except BaseException as error:
        telemetry.update(status="REFUSED", reason=type(error).__name__ + ": " + str(error))
        raise
    finally:
        if previous is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
            if timer and timer[0]:
                signal.setitimer(signal.ITIMER_REAL, max(0.001, timer[0] - (time.monotonic() - started)), timer[1])
        if owns_lock:
            telemetry.update(elapsed_seconds=time.monotonic() - started,
                             peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            path = output / ("cpu_telemetry_" + attempt + ".json")
            with path.open("x") as handle:
                json.dump(telemetry, handle, sort_keys=True, allow_nan=False)
                handle.write("\n")
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--frame-root", action="append", required=True)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--memory-gib", type=int, default=30)
    parser.add_argument("--max-seconds", type=int, default=21600)
    parser.add_argument("--sample-size", type=int, default=64)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    prepare(args.config, args.config_sha256, args.output, args.frame_root,
            threads=args.threads, memory_gib=args.memory_gib, max_seconds=args.max_seconds,
            sample_size=args.sample_size, resume=args.resume)
    print(json.dumps({"status": "PREPARED", "store_published": False, "cross_run_adoptable": False}))


if __name__ == "__main__":
    main()
