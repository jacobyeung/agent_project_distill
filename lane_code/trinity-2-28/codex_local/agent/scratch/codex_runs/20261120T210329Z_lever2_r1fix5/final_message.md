Rebuilt, but **not ready for resubmission**.

- Added the early source gate and capture-local staging: [s.py:7](runtime/s.py:7).
- Runs tower 1 before carrier loading and flushes its depth before staging capture 2: [w.py:117](runtime/w.py:117).
- Records per-capture RSS, GPU peak allocation, elapsed time, and incomplete status: [m.py:29](runtime/m.py:29).
- Forecast: **23.75 worker / 37.75 allocation minutes**. The two-minute GPU failure bound remains unverified.

Syntax, package seals, naming scans, and checksums passed. Full CPU tests—including rehearsal and capture doubles—remain pending.

Token: `a784b94c2e6af`  
Delivery: **3,704,563 bytes**  
SHA256: `fba95b8b0b00c87ec7900817a0977084e18efed504b8918e24eccf9224302974`

May I move old fixtures to `/tmp`, preserving every file? [BRIEF_R1.md](../BRIEF_R1.md) limits this workspace to 2 GB and makes other locations read-only; current contents leave insufficient room for the required reruns.