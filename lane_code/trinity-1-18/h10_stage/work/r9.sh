B=/scratch/jjyeung/orch_n30/b04_e2ehook
cd $B && find e2e_reader heads parity_kit -name '*.py' -not -path '*/__pycache__/*' -not -path '*/tests/*' -exec sha256sum {} \; | sort -k2 >&2
grep -rn "sl118" $B/STATUS.md $B/out/E2E_READER_READY.md 2>/dev/null | head -10 >&2
ls -la $B/heads/selector/sl118 >&2
tar cf - -C $B heads/selector/sl118
