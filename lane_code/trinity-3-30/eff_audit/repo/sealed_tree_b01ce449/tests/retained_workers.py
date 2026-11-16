import multiprocessing
import socket
import sys
import time


def retain_files(event, arguments):
    if event in ("os.remove", "os.rmdir"):
        raise PermissionError("The test retains its artifacts")


def invoke(function, rank, arguments, audit):
    sys.addaudithook(audit)
    function(rank, *arguments)


def run_workers(function, arguments, world=2, timeout=180, start_method="spawn"):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    context = multiprocessing.get_context(start_method)
    audit = getattr(sys.modules["__main__"], "audit", retain_files)
    workers = [context.Process(target=invoke, args=(function, rank, (*arguments, port), audit))
               for rank in range(world)]
    for worker in workers:
        worker.start()
    deadline = time.monotonic()+timeout
    try:
        for worker in workers:
            worker.join(max(0, deadline-time.monotonic()))
        if any(worker.is_alive() for worker in workers):
            raise TimeoutError("Native CPU test workers exceeded their deadline")
        if any(worker.exitcode != 0 for worker in workers):
            raise RuntimeError("Native CPU test workers failed: "+str([worker.exitcode for worker in workers]))
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
        for worker in workers:
            worker.join()
