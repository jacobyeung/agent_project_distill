"""Check native training_text supervision boundaries for visible and null real-row targets."""
import json, resource, sqlite3, sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
TREE=ROOT/'work/final'
sys.path.insert(0,str(TREE))
resource.setrlimit(resource.RLIMIT_AS,(38*1024**3,38*1024**3))
import torch
torch.set_num_threads(16)
from student_pilot.batches import training_text
from student_pilot.carrier_c1_data import pointing_token_weights
from student_pilot.pointing_locate import RULE_PIN, render
from student_pilot.p3_provenance import sha256

source=ROOT.parent/'in/pointing/rows_c09bb5ca.sqlite'
comparison=ROOT/'out/COMPARE.json'
spec=json.loads(comparison.read_text())
records=[]
class Processor:
    tokenizer=SimpleNamespace(eos_token='<|im_end|>',eos_token_id=1)
    def __init__(self, prefill):self.prefill=prefill
    def apply_chat_template(self, messages, *, add_generation_prompt, **kwargs):
        stem='<|im_start|>assistant\n'
        return (stem+('<think>\n' if self.prefill else '') if add_generation_prompt else
                stem+messages[-1]['content']+self.tokenizer.eos_token+'\n')
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as conn:
    for kind,sample in spec['real_stored_targets']['samples'].items():
        row=json.loads(conn.execute('SELECT row FROM rows WHERE i=?',(sample['i'],)).fetchone()[0])
        answer=row['target'].split('</think>\n\n')[1]
        target=render(row,answer)
        for prefill in (False,True):
            prompt,suffix=training_text(Processor(prefill),row['student_input']['question'],[],target)
            assert suffix.startswith('Locate the' if prefill else '<think>\nLocate the')
            labels=torch.tensor([[-100,*map(ord,suffix),-100]])
            weights=pointing_token_weights(labels,chr,pointing_locate=RULE_PIN)
            index=int(weights.argmax());selected=chr(int(labels[0,index]))
            assert selected==(':' if kind=='null' else '.')
            assert index==1+suffix.index(f"in frame {row['pointing']['frame']}")+len(f"in frame {row['pointing']['frame']}")
            assert abs(float(weights[labels!=-100].mean())-2)<1e-5
            assert abs(float(weights[0,index]/weights[0,1])-5)<1e-5
            records.append(dict(kind=kind,source_i=sample['i'],qid=row['qid'],opening_think_in_masked_prompt=prefill,
                first_supervised_characters=suffix[:32],weighted_token=selected,label_index=index,
                normalized_decision_weight=float(weights[0,index]),supervised_mean=float(weights[labels!=-100].mean())))
inputs={str(p):sha256(p) for p in (source,comparison,Path(__file__))}
for mod in tuple(sys.modules.values()):
    p=getattr(mod,'__file__',None)
    if p and Path(p).is_file() and Path(p).is_relative_to(TREE):inputs[p]=sha256(p)
record=dict(command='bash code/run.sh boundary_probe',input_sha256=inputs,status='PASS',cases=records,
    scope='Real visible/null stored targets through native training_text and pointing_token_weights; synthetic chat-template/character-tokenizer fixtures cover both opening-think boundaries. No production tokenizer claim.')
(ROOT/'out/TRAINING_BOUNDARY.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS',len(records),'native training_text boundary/decision cases')
