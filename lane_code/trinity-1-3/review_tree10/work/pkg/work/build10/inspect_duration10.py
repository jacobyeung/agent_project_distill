from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
for root in (L/'work/build10',L.parent/'w9f/work/build9fix'):
    for variant in ('suite_tree','suite_base'):
        p=root/'proofs'/variant/'temporary_sizes.json'
        if p.is_file():
            for r in json.loads(p.read_text()):
                if 'test_bf16_all_world_four_first_batches_with_and_without_checkpointing' in r['test']:
                    print(str(p),json.dumps(r))
