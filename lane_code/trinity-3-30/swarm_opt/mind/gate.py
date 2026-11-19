"""Stop until the governor continues this process, then run the reader command as a child and wait (never exec)."""
import os, signal, subprocess, sys
os.kill(os.getpid(), signal.SIGSTOP)
sys.exit(subprocess.call(sys.argv[1:]))
