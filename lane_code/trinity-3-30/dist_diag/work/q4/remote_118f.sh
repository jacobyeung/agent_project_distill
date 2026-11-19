#!/bin/bash
set -u
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1
echo "== files"; ls $T; ls $T/trace_format | head -30
echo "== grep question_identity / question in trace_format + generator (bounded tree)"
timeout 60 grep -rn "question_identity\|def validate_evidence\|record\[.question.\]\|row\[.question.\]\|\"question\"\]" $T/trace_format $T/student_pilot $T/generator 2>/dev/null | cut -c1-220 | head -40
G=$T/trace_format/ground_v312.py
echo "== validate_evidence"; awk '/^def validate_evidence/,/^def [a-z_]+\(/' $G | head -120
echo "== done $(date -u +%FT%TZ)"
