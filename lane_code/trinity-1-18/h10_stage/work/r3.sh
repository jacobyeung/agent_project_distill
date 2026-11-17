B=/scratch/jjyeung/orch_n30/b04_e2ehook
{
echo "== status sam refs"; grep -n -i -E "sam3|SAM3_RECEIPT|sam3\.pt|receipt" $B/STATUS.md 2>/dev/null | head -40
echo "== find receipts"; find $B -maxdepth 6 \( -name 'SAM3_RECEIPT*' -o -name 'sam3.pt' -o -name '*sam3*receipt*' \) 2>/dev/null | head -20
ls -la $B/heads/selector/work/run_iso/ $B/work/n13/obj/ 2>&1 | head -30
} >&2
tar cf - -C / ${B#/}/heads/selector/work/run_iso/selector_head.json ${B#/}/heads/selector/work/run_iso/selector_head.safetensors ${B#/}/work/n13/obj/model_8005668fc14ce5ee.tar ${B#/}/work/n13/obj/base_small.tgz
