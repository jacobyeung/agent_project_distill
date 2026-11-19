from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'work/b21_final/work/tree_r1/tests/test_so_round3.py'
s=p.read_text().replace('        model = native()\n        optimizer', '        model = native()\n        run.SKIPPED.update(skipped=0, total=0)\n        optimizer');p.write_text(s)
p=ROOT/'out/kit_timing/data_only.py';s=p.read_text().replace('import argparse\n','import argparse\nimport hashlib\n')
s=s.replace('            result.append(dict(step=step,wall_seconds=', "            result.append(dict(step=step,plan_sha256=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),wall_seconds=")
s=s.replace("        start_step=frozen.get('start_step',0), resume=frozen.get('resume'),", "        start_step=frozen.get('start_step',0), resume=frozen.get('resume'), config_sha256=run.identity(cfg),")
p.write_text(s)
p=ROOT/'out/kit_timing/replay_compare.py';s=p.read_text().replace("or meta['rank'] != rank", "or meta['config_sha256'] != manifests[0]['config_sha256']\n                    or data[0]['plan_sha256'] != records[0]['plan_sha256']\n                    or meta['rank'] != rank")
s=s.replace("if (meta['start_step']", "if (len(data) != 10 or meta['start_step']")
s=s.replace("rule='bitwise' if stable else 'each loss within both OFF values plus their absolute spread'", "rule='bitwise' if stable else 'both absolute ON-to-OFF differences <= the OFF-to-OFF spread'")
p.write_text(s)
