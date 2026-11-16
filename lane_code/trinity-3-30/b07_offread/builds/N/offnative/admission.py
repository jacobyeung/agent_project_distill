"""Enumerate concrete input failures before a production packet can be admitted."""
from pathlib import Path
import re
from .io import load, sha
from .staging import validate_media
from .source import bind_source


def check(binding, inputs):
    reasons=[]
    if binding['mode']=='fixture':reasons.append('fixture binding is ineligible for production')
    if binding['benchmark']!='revsi999t32':reasons.append('VSI-Bench worker is not implemented')
    if not isinstance(inputs,dict):
        inputs={}
        reasons.append('missing input: production input manifest (--inputs)')
    kind=binding['reader']['kind']
    required=['export','runtime','base','media_manifest','proof_original_export','proof_assets','bwrap']
    required+=['g3t_weights','g3t_config','sam3_weights','sam3_source','selector'] if kind=='harness' else ['e2e_artifact','e2e_loaded_entry']
    for name in required:
        value=inputs.get(name)
        if not isinstance(value,dict):
            reasons.append('missing input: '+name);continue
        if not re.fullmatch('[0-9a-f]{64}',value.get('sha256','')):
            reasons.append('missing input: '+name+'.sha256')
        if not value.get('logical_path') or Path(value['logical_path']).is_absolute() or '..' in Path(value['logical_path']).parts:
            reasons.append('missing input: '+name+'.relative logical_path')
        if not isinstance(value.get('bytes'),int) or value.get('bytes',0)<=0:
            reasons.append('missing input: '+name+'.bytes')
        if not value.get('source'):
            reasons.append('missing input: '+name+'.uploaded source')
        if value.get('bytes',0)>20_000_000 and not value.get('transfer_receipt'):
            reasons.append('missing input: '+name+'.governed transfer receipt')
    if kind=='harness':
        freeze=binding['reader']['freeze_values']
        if freeze.get('g3t_source')!=binding['read_config']['g3t']['source']:
            reasons.append('missing input: P8 freeze_values.g3t_source')
        if inputs.get('sam3_weights',{}).get('sha256')!='9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e':
            reasons.append('SAM 3 weights do not have the frozen SHA256')
        for field in ('proposal_setting','candidate_policy','fusion_policy','depth_cut','box_rule','room_rule','gravity_guard','selector'):
            if field not in freeze:reasons.append('missing input: P8 freeze_values.'+field)
    media=inputs.get('media',[])
    expected=302 if binding['benchmark']=='revsi999t32' else 288
    if len(media)!=expected:reasons.append('missing input: complete media manifest ('+str(expected)+' videos)')
    for name in validate_media(media,production=False)['missing']:
        reasons.append('missing input: media hash/bytes for '+name)
    for row in media:
        if row.get('uploaded') is not True:reasons.append('missing input: uploaded media receipt for '+row['relative_path'])
    if kind=='harness' and binding['read_config']['g3t']['source']=='original' and not inputs.get('original_mapping'):
        reasons.append('missing input: original_mapping')
    for name in ('uploaded_media_root','extra_files','config','artifact','data_receipt',
                 'label_file','media_root','proof_keys'):
        if not inputs.get(name):reasons.append('missing staged input: '+name)
    if kind=='harness' and binding['read_config']['frames']['count']!=32:
        reasons.append('C8r cache/geometry contract supports 32 anchors; a 64-anchor implementation is unavailable')
    return reasons
