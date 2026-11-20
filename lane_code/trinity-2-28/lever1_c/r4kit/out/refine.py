from pathlib import Path
p=Path('src/control.py');s=p.read_text()
s=s.replace("    old = signal.getsignal(signal.SIGALRM)\n", "    old = signal.getsignal(signal.SIGALRM)\n    previous_timer = signal.getitimer(signal.ITIMER_REAL)\n    entered = time.monotonic()\n")
s=s.replace("        signal.signal(signal.SIGALRM, old)\n", "        signal.signal(signal.SIGALRM, old)\n        if previous_timer[0]:\n            signal.setitimer(signal.ITIMER_REAL, max(.001, previous_timer[0]-(time.monotonic()-entered)), previous_timer[1])\n")
s=s.replace("        J, local = prepare(p, root, cfg, job, min(end, started+600))\n        code = launch(root, local, cfg, mode, end, J)", "        with bounded(min(end, started+600), 600):\n            J, local = prepare(p, root, cfg, job, min(end, started+600))\n        with bounded(end+5, 1735):\n            code = launch(root, local, cfg, mode, end, J)")
p.write_text(s)
p=Path('tests/test_fixes.py');s=p.read_text().replace("                    (root/'p/a').mkdir(parents=True)\n                    if case in", "                    if case in").replace("                        # A finished pair", "                        (root/'p/a').mkdir(parents=True)\n                        # A finished pair")
p.write_text(s)
