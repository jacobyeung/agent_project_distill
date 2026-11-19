"""Generated v3.12.1 rows through native RGB encoding and tiny Qwen routing loss."""
import copy
import json
from pathlib import Path
import sys

lane = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'tools' else Path(__file__).resolve().parent
# This script is copied into the integrated tools directory after row-contract integration.
tree = lane/'c1mix_e2e' if (lane/'c1mix_e2e').is_dir() else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tree))
import numpy as np
from PIL import Image
import torch
from transformers import Qwen3_5ForConditionalGeneration
from student_pilot import carrier_c1_run as run, carrier_c1_routing as routing, carrier_c1_data as data, ground_tokens, mdg_lora
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.e2e_routing_rows import adapt_generated
from student_pilot.p3_provenance import file_pin
from tests.test_carrier_c1_final import final_fixture


def check(source, output, fixture_root):
    torch.set_num_threads(1)
    cfg=json.loads((tree/'configs/E2E-1G.json').read_text())
    receipt=dict(training_mode='final', frame_markers=True, mdg=cfg['mdg'])
    processor=run.processor_for_receipt(dict(root='/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor'),receipt)
    template,_,_=final_fixture()
    config=copy.deepcopy(template.config)
    config.text_config.vocab_size=248320
    config.text_config.pad_token_id=processor.tokenizer.pad_token_id
    config.text_config.eos_token_id=processor.tokenizer.eos_token_id
    config.vision_config.patch_size=16
    config.video_token_id=processor.tokenizer.convert_tokens_to_ids('<|video_pad|>')
    config.image_token_id=processor.tokenizer.convert_tokens_to_ids('<|image_pad|>')
    config.vision_start_token_id=processor.tokenizer.convert_tokens_to_ids('<|vision_start|>')
    config.vision_end_token_id=processor.tokenizer.convert_tokens_to_ids('<|vision_end|>')
    base=Qwen3_5ForConditionalGeneration(config).float()
    from student_pilot.camera_targets import carrier_id
    depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=4,context_depth=1,vit_layers=[1,2,3])
    model=CarrierC1(base,template.auxiliary_heads.pose.settings,depth,carrier_id(processor.tokenizer),data.C1_A,
                    'final',True,cfg['recipe'],frame_layout='duplicate',depth_fov_source='pose_head').eval()
    routing.init_routing_embeddings(model,processor._routing_tokens)
    ground_tokens.initialize(model,processor)
    model.mdg_tokenizer=processor.tokenizer
    mdg_lora.install(model,32);ground_tokens.install_rows(model)
    rows=[json.loads(line) for line in Path(source).read_text().splitlines() if line.strip()]
    chosen={}
    text_cost=lambda row: len(processor.tokenizer.encode(row['question']+'\n'+'\n'.join(row['options'])+'\n'+row['suffix'],add_special_tokens=False))
    for row in rows:
        if row['type'] not in chosen or text_cost(row)>text_cost(chosen[row['type']]):
            chosen[row['type']]=row
    report=[]
    fixture_root=Path(fixture_root);fixture_root.mkdir(parents=True,exist_ok=True)
    frames=[]
    for k in range(32):
        path=fixture_root/f'rgb_{k:02d}.png'
        Image.fromarray(np.full((128,128,3),(k*7)%255,np.uint8)).save(path)
        frames.append(file_pin(path))
    for qtype,row in sorted(chosen.items()):
        indices=row['frame_indices'];fps=30.
        inputs=dict(frames=frames,frame_indices=indices,timestamps=[i/fps for i in indices],fps=fps,
                    total_num_frames=max(indices)+1,question=row['question'],options=row['options'],recording_id=row['scene'])
        packed=adapt_generated(row,inputs,dataset='scannet',scene=row['scene'])
        batch, audit=routing.encode(processor,packed,data.C1_A,'final','duplicate',None)
        run.check_row(batch,None,'routing',model)
        with torch.no_grad():result=model(batch,None,stream='routing')
        assert torch.isfinite(result['loss'])
        tags=batch['aux_segments']
        tool=tags==routing.SEGMENTS.index('tool')
        assert tool.any() and (batch['labels'][tool]==-100).all()
        assert int((batch['aux_camera_positions']>=0).sum())==32
        report.append(dict(qid=row['qid'],type=qtype,tokens=batch['input_ids'].shape[-1],
            suffix_tokens=audit['suffix_tokens'],trained_tokens=audit['trained_tokens'],
            tool_spans=audit['tool_spans'],loss=float(result['loss']),finite=True,
            over_10k_tokens=batch['input_ids'].shape[-1]>10000,frames=32,
            diagnostic_only=row.get('diagnostic_only'),training_admitted=row.get('training_admitted')))
    result=dict(status='PASS',input_status='PENDING-INPUT: RGB and 9B weights replaced by explicit native CPU fixtures',
        generated_rows=str(source),processor='/scratch/jjyeung/orch_cd/p3_build/fixtures/qwen35_processor',
        atomic_openers=model.ground_token_ids,records=report,largest_row=max(report,key=lambda r:r['tokens']),
        selection='Longest native-tokenized question/options/suffix text per type in the supplied fixture',
        candidate_rows=len(rows),revisions=sorted({row['spec_version'] for row in rows}),
        geometry='Generated five-scene GT-mask/GT-geometry traces; source training-admission flags retained')
    Path(output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    check(sys.argv[1],sys.argv[2],sys.argv[3])
