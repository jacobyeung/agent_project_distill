cd /scratch/jjyeung/orch_n30/sb_own400 && diff kit/score_400.py kit/score_400b.py; sha256sum kit/score_400b.py kit/test_400b.py | cut -c1-16,65-; head -c 1500 out/KIT_REPORT_B.md 2>/dev/null; ls out/
