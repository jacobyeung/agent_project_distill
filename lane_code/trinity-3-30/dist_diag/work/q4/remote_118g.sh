#!/bin/bash
set -u
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/tree_r1
G=$T/trace_format/ground_v312.py
echo "== validate_evidence"; sed -n '/^def validate_evidence/,/^def [a-z]/p' $G | head -90
echo "== question_identity defs"
timeout 60 grep -rn "def question_identity\|def normalized\b\|def agrees" $T/generator $T/trace_format 2>/dev/null | head
Q=$(timeout 60 grep -rln "def question_identity" $T/generator 2>/dev/null | head -1); echo "Q=$Q"
[ -n "$Q" ] && sed -n '/^def question_identity/,/^def [a-z]/p' "$Q" | head -30 && sed -n '/^def normalized/,/^def [a-z]/p' "$Q" | head -30
A=$(timeout 60 grep -rln "def agrees" $T/generator 2>/dev/null | head -1); echo "A=$A"; [ -n "$A" ] && sed -n '/^def agrees/,/^def [a-z]/p' "$A" | head -20
echo "== grep question in ground_v312.py / ground_v313.py"; grep -n "question" $G $T/trace_format/ground_v313.py | head -20
echo "== done $(date -u +%FT%TZ)"
