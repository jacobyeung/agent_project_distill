from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix'
p=B/'write_report.py';text=p.read_text()
text=text.replace('The scale loss weight remains 1.0.', 'The config keeps the scale loss on at weight 1.0 (GUESS for the actual D0 runtime weight; the prior kit supplied this choice). Actual D0 scale settings remain a named blocker.')
text=text.replace('work/n1fix/inputs/room_validator.json','work/n1fix/inputs/room_v2_CHECK.json')
text=text.replace('as required by the card and the room-program admission refusal', 'as required by the user brief and the room-program admission refusal; their source count is documented in `work/design/NEXT_LEG_INIT_RULE_20261116.md`')
p.write_text(text)
p=B/'DECISIONS.md';text=p.read_text()
text+='\n## Open decisions and defaults\n\n| Decision | Options | Default used |\n|---|---|---|\n'
text+='| VQA version | v6; v7 with passing producer validator | v7 receipt; full intake and remote location still required. |\n'
text+='| Size and room cells | Admit eligible sources; defer | Defer with zero cells and move released slots to direction. |\n'
text+='| Missing processor and lineage evidence | Infer; block | Block; no default resolution or fabricated legality record. |\n'
text+='| Scale runtime weight | Supplied kit choice; infer D0 runtime | Keep the supplied kit choice of 1.0 as GUESS; require the actual runtime value before launch. |\n'
text+='| P inference export | Restart schedule; preserve progress | Preserve absolute LR and sampler progress; optimizer moments start fresh. |\n'
text+='| Local result publication | External event write; stage locally | Stage one review request locally under out/RESULT_build_n1.json. |\n'
p.write_text(text)
