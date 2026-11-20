"""Record the unchanged native contract before any rehearsal stage runs."""
import ast
from pathlib import Path

def decide(root,kit,J):
    source=root/'source/student_pilot'
    scene=source/'r2_scene_bindings.py'
    twins=source/'r1_direction_twins.py'
    mix=source/'r1_mix.py'
    assert 'index >= 2000' in scene.read_text()
    assert 'COUNT = 7971' in twins.read_text()
    assert "card.get('steps') != 1000" in mix.read_text()
    assert '4*counts[k]' in mix.read_text()
    assert "'vqa': 128" in (source/'r1_training.py').read_text()
    assert "'vqa': 'vqa'" in scene.read_text()
    evidence={str(p):J.sha(p) for p in [scene,twins,mix,source/'r1_training.py',source/'r1_population.py',kit/'b/sc.py',kit/'b/pl.py']}
    J.write(root/'CAPACITY_SOURCES.json',dict(kit_seal=J.seal(kit),sources=evidence,
        scene_limit=2000,vqa_minimum_rows=32000,native_twins=7971,possible=False,
        evidence_kind='source arithmetic; no native execution or bypass'))
    lines=[
        'No fixture within the native 2,000-row scene limit can satisfy the unchanged sampler.',
        f'{scene}:15-16 maps VQA, camera, pointing and both pose families into scene rebuilding; {scene}:49-65 enforces 2,000 decoded rows per family on Trinity, including SQLite rows.',
        f'{kit}/b/sc.py:20-27 uses each stream receipt and its count, selecting rows_metadata or the database; {scene}:140-159 requires that metadata pin and count to match the input receipt and counts the entire population. A metadata projection cannot claim 32,000 rows after decoding only 2,000.',
        f'{source}/r1_training.py:7 assigns 128 VQA draws per step. {mix}:10,24-42 fixes 1,000 steps and caps each eligible row at four draws. Thus VQA needs at least 128*1000/4 = 32,000 rows; 2,000 rows supply at most 8,000 of 128,000 draws.',
        f'{source}/r1_population.py:154 validates the full allocation even when asked for one step. Reducing the rehearsal loop length does not reduce this admission requirement.',
        f'{twins}:11,44 requires exactly 7,971 bindings. {twins}:98-106 requires the augmented database to contain every base row followed by every twin. The twins alone exceed 2,000; this fixture has distinct sources, requiring 15,942 rows for all pairs.',
        'The requested conjunction of every native invariant and the scene limit is therefore impossible. The single attempt supplies 1,000 complete source/twin pairs, authenticates the matching subset binding and augmentation receipt, and leaves COUNT, scene limits, removals, admission and resolver checks unchanged.',
        'The expected first refusal is R1_TWIN_BINDING_COUNT during native census. This is a native-contract incompatibility for bounded Trinity rehearsal, not evidence of a production-kit failure. The sampler shortfall is proved from source and may not be reached by this attempt.',
        'CAPACITY_SOURCES.json records the selected kit seal and source digests. No retry is authorized by this decision.'
    ]
    with (root/'CAPACITY_DECISION.md').open('x') as f:f.write('\n'.join(lines)+'\n')
