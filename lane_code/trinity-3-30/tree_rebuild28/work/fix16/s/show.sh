#!/bin/bash
# compact view of a poll output: steps after the selection
f=$1
grep -v '^{"remove_list\|^{"source\|^{"pool_rows\|^{"admitted_census' "$f" | cut -c1-${2:-330} | grep -v "^total\|^d.* \.$\|^d.* \.\.$" | sed -n '/== q.err/,$p' | grep -v "^== planned\|^== SELECTION\|rows.sqlite sha256 5e35\|^== p$\|plan.json\| i$\| s$\| e$\|e.json$\| f$\|n.json$\| sc$\|source_code.json\|ss.json\|t.tar\| u$\| w$\| y$\|scene rebuild seconds\|A15_SELECTION\|fast path is not available\|^== p/q/selection\|materialization.json$\| pool$\|34057 .* receipt.json\|849543168\|^== p/q/twins\|augmentation.json\|805 .* receipt.json\|4655 .* room_audit.json\|1791614976\|twins/room_audit.json bytes"
