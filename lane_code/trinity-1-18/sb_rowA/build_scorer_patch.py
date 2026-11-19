"""Create an isolated camera-placement patch and exercise the production scorer on CPU."""
import copy,difflib,importlib.util,json,sys
from camera_contract import ROOT,OUT,BASE,load,pin,save,frozen,INPUTS,sha
READ=BASE/'sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src'
PATCH=OUT/'SCORER_PATCH'
def main():
 frozen();pin(__file__)
 PATCH.mkdir(exist_ok=True);(PATCH/'h1eval').mkdir(exist_ok=True)
 path=READ/'h1eval/scorers.py';pin(path);old=path.read_text()
 needle="    meta=metadata(item);expected=expected_calls(meta['question'],meta['question_type']);got=records(output)"
 replacement="""    meta=metadata(item)
    kind=meta['question_type']
    if kind in ('camera_displacement','camera_rotation','camera_movement_direction'):
        pair=meta.get('display_frame_pair')
        if (not isinstance(pair,(list,tuple)) or len(pair)!=2
                or any(type(v) is not int for v in pair)):
            raise ValueError('camera_item_missing_display_frame_pair')
        i,j=pair
        if not 1<=i<j<=32:
            raise ValueError('camera_item_invalid_display_frame_pair')
        expected=[f'<{"turn" if kind=="camera_rotation" else "move"} from={i} to={j}>']
    else:
        expected=expected_calls(meta['question'],kind)
    got=records(output)"""
 assert old.count(needle)==1
 new=old.replace(needle,replacement)
 target=PATCH/'h1eval/scorers.py';target.write_text(new)
 (PATCH/'placement.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/h1eval/scorers.py',tofile='b/h1eval/scorers.py')))
 for path in (READ,READ/'b'):sys.path.insert(0,str(path))
 from h1eval import scorers,runner
 from h1eval.items import load_manifest
 from rows.expected_calls import expected_calls
 spec=importlib.util.spec_from_file_location('camera_patched_scorers',target);patched=importlib.util.module_from_spec(spec);spec.loader.exec_module(patched)
 orig=load(READ/'items/devs1_routed.json');held=load(OUT/'HELDOUT_CAMERA_ITEMS.json')
 assert len(orig['items'])==636
 def stub(calls,answer):
  records=[dict(call=c,response='turn = +10 deg' if c.startswith('<turn') else 'dx = +1.00 m, dy = +0.00 m, dz = +0.10 m, distance = 1.00 m',at_token=5,served=True) for c in calls]
  return dict(text='<think>'+''.join(calls)+'</think><answer>'+str(answer)+'</answer>',calls=records,finish='eos',tokens=[])
 parity=0;cases=0;camera_equal=0
 for item in orig['items']:
  calls=expected_calls(item['question'],item['question_type'])
  if item['question_type'].startswith('camera_'):
   i,j=item['display_frame_pair'];assert calls==[f'<{"turn" if item["question_type"]=="camera_rotation" else "move"} from={i} to={j}>'];camera_equal+=1
  # Compare all M1 fields, including absent, repeated, extra, reordered and wrong calls.
  variants=[calls,[],calls+calls,list(reversed(calls)),['<move from=1 to=2>'],calls+['<turn from=1 to=2>']]
  for cs in variants:
   out=stub(cs,item['answer']);assert scorers.placement(out,item)==patched.placement(out,item);cases+=1
  parity+=1
 admitted=load_manifest(str(OUT/'HELDOUT_CAMERA_ITEMS.json'));assert admitted['count']==900
 for name in list(sys.modules):
  if name=='e2e_reader' or name.startswith('e2e_reader.'):sys.modules.pop(name)
 sys.path.insert(0,str(READ/'b'))
 from h1eval.h10.parity_adapter import map_items
 mapped,mapping=map_items(admitted['items'],dict(tasks=[str(OUT/'HELDOUT_NATIVE_TASKS.jsonl')],frames_root='/scratch/jjyeung/devs1_frames'),name=admitted['name'])
 assert len(mapped)==len(mapping['items'])==len({r['key'] for r in mapping['items']})==900
 # Point the runner at the isolated patched scorer module for this CPU check.
 assert runner.scorers is scorers
 runner.scorers=patched
 count=0
 for item in held['items']:
  i,j=item['display_frame_pair'];call=f'<{"turn" if item["question_type"]=="camera_rotation" else "move"} from={i} to={j}>'
  result=runner.measure(stub([call],item['answer']),item)
  assert result['M1']['exact'] is True
  count+=1
 # Explicit metadata refusal: never fall back to parsing question text.
 item=next(x for x in held['items'] if x['question_type']=='camera_rotation')
 invalid=[None,[],[1],[1,2,3],['1',2],[True,2],[0,2],[2,2],[3,2],[1,33]]
 for pair in invalid:
  bad=dict(item,display_frame_pair=pair)
  try:patched.placement(stub([],bad['answer']),bad)
  except ValueError:pass
  else:raise AssertionError(pair)
 for file in ['h1eval/scorers.py','rows/expected_calls.py','h1eval/runner.py','h1eval/items.py','h1eval/h10/parity_adapter.py','h1eval/h10/merge.py']:pin(READ/file)
 for file in [target,PATCH/'placement.patch']:pin(file)
 frozen()
 save(PATCH/'CHECKS.json',dict(status='PASS',command='/scratch/jjyeung/envs/p1cpu/bin/python -B build_scorer_patch.py',devs1_items=parity,M1_parity_cases=cases,camera_original_expected_calls_equal=camera_equal,heldout_stub_measure_scored=count,native_manifest_items=900,native_mapped_unique_keys=900,invalid_pairs_refused=len(invalid),production_files_modified=False,independent_review='PENDING: cont_ops18 must obtain review before applying and sealing',patch_file='placement.patch',patched_files=['h1eval/scorers.py']))
 print(json.dumps(dict(parity=parity,cases=cases,heldout_scored=count,native_mapped=len(mapped))))
if __name__=='__main__':main()
