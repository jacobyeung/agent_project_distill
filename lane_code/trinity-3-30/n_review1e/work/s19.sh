T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp/student_pilot; cd $T
grep -n -E "get\('(ground_record|tool_output_spans|routing|events)'" row_text_audit.py | head; L=$(grep -n "def recorded_responses" row_text_audit.py | cut -d: -f1); sed -n "${L},$((L+14))p" row_text_audit.py
echo ==== extent; grep -n -E "get\('(question_type|ground_record|provenance|routing|type|answer_form)'|\['routing'\]" extent_receipt.py | cut -c1-200
L=$(grep -n "def check" extent_receipt.py | head -1 | cut -d: -f1); sed -n "${L},$((L+25))p" extent_receipt.py
echo ==== coverage; grep -n -E "get\('(ground_record|routing|student_input|canonical)'" r1_coverage.py | cut -c1-200
echo ==== r2_contract; grep -n -E "get\('(provenance|ground_record|question_type|qid|dataset)'" r2_contract.py | cut -c1-200; grep -n "def check" -A12 r2_contract.py | head -30
