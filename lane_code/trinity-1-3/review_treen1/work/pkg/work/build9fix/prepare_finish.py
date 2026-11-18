import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
for name in ('legacy_guard_proof.py','inference_inventory.py'):
    (B/name).write_text((L/'work/build9'/name).read_text().replace('work/build9','work/build9fix'))
audit=B/'proofs/audit';audit.mkdir(parents=True,exist_ok=True)
(audit/'INFERENCE_COMPONENTS.json').write_bytes((L/'work/build9/proofs/audit/INFERENCE_COMPONENTS.json').read_bytes())
text=(B/'DECISIONS.md').read_text()
(B/'DECISIONS.md').write_text('\n\n'.join(dict.fromkeys(text.strip().split('\n\n')))+'\n\n'
 '- P exports carry inference weights, so continuation preserves the absolute schedule and row plans but starts fresh optimizer moments. A real P boundary receipt must bind the export, configuration, every store and the row plan. Different plans refuse.\n'
 '- Preserve routing opener weights only with the matching vocabulary witness; the missing production witness stays a named launch input.\n'
 '- The authoritative n1 report is out/BUILD_R1_REPORT.md. The requested BUILD9_REPORT.md path receives a compatibility pointer to the preserved build-9 report and this report. The design ledger receives Build n1.\n')
(B/'STATUS.md').write_text('# Build n1 status\n\nR1 native configuration validation passes. The source, init metadata, receipt-selected VQA store, routing-source pins and opaque GO=false packet are bound. The packet suite is running; a final run is required after harness fixture references and final source bindings. Frozen-package suites will reuse only matching base-group receipts.\n\nThe loader audit is bounded and BLOCKED on full scene coverage, all-stream populations, frame-host preparation and row plans. The launch binding table is work/build9fix/BINDING_TABLE.md.\n')
