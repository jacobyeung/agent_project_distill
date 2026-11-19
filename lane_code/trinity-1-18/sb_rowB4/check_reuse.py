"""Check the B3 algorithms and authorities that this task requires unchanged."""
import ast,json
from pathlib import Path
from stage_inputs import sha
ROOT=Path(__file__).resolve().parent;B3=ROOT.parent/'sb_rowB3';OUT=ROOT/'out'
def functions(path):
    source=path.read_text()
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def main():
    preserved={
      'build_rows.py':['rank_cell','semantics','geometry','hist','balanced_schedule'],
      'base_rows.py':['canonical_bytes','dh','normalize','load_rows','room_authorities','room_reasons','WordingFilter','option_permutation'],
    }
    pins={str(Path(__file__)):sha(Path(__file__))}
    for name,names in preserved.items():
        a=functions(B3/name);b=functions(ROOT/name)
        for n in names:assert a[n]==b[n],(name,n)
        for p in [B3/name,ROOT/name]:pins[str(p)]=sha(p)
    for name in ['wording_filter.cpp','stage_inputs.py','inputs/wording_filter.so','inputs/WORDING_CORPUS.json','inputs/dev_scene_exclusions.json','inputs/GT_FACTS.jsonl','inputs/GT_REFUSALS.json','inputs/GT_RESOLUTION.json','inputs/sources.jsonl']:
        a=sha(B3/name);b=sha(ROOT/name);assert a==b,name
        pins[str(B3/name)]=a;pins[str(ROOT/name)]=b
    result={'status':'PASS','input_sha256':pins,'unchanged_functions':preserved,'unchanged_inputs':'wording code/corpus, room exclusions, original source rows and GT facts/resolution/refusals; SHA256-equal to B3'}
    (OUT/'B3_INVARIANTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('B3 retained algorithms and input hashes: PASS')
if __name__=='__main__':main()
