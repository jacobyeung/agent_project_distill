"""Enumerate concrete input failures before a production packet can be admitted."""
from pathlib import Path
import re
from .io import load, sha
from .staging import validate_media
from .source import bind_source


def check(binding, inputs):
    reasons=[]
    if binding['mode']=='fixture':reasons.append('fixture binding is ineligible for production')
    if not isinstance(inputs,dict):
        inputs={}
        reasons.append('missing input: production input manifest (--inputs)')
    kind=binding['reader']['kind']
    required=['export','runtime','base','media_manifest','proof_original_export','proof_assets','bwrap','offkit']
    if binding['benchmark']=='revsi999t32':required.append('revsi_archive')
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
        if binding['read_config']['g3t']['source']=='clip32':
            reasons.append('clip32 is diagnostic only; production refused')
    media=inputs.get('media',[])
    expected=302 if binding['benchmark']=='revsi999t32' else 288
    if len(media)!=expected:reasons.append('missing input: complete media manifest ('+str(expected)+' videos)')
    for name in validate_media(media,production=False)['missing']:
        reasons.append('missing input: media hash/bytes for '+name)
    for row in media:
        if row.get('uploaded') is not True:reasons.append('missing input: uploaded media receipt for '+row['relative_path'])
    if binding['benchmark']=='revsi999t32':
        manifest=inputs.get('revsi_media_manifest')
        if not manifest or not Path(manifest).is_file():
            reasons.append('missing input: revsi_media_manifest with both clip sets')
        else:
            value=load(manifest)
            if value.get('hashes_pending') or any(not r.get('sha256') for r in value.get('files',[])):
                reasons.append('ReVSI clip hashes pending; production refused')
            if len(value.get('files',[]))!=604:reasons.append('ReVSI media manifest must cover both 302-clip sets')
        if binding['read_config']['g3t']['source']=='original':
            mapping=inputs.get('original_mapping')
            if not mapping or not Path(mapping).is_file():reasons.append('missing input: original_mapping')
            else:
                from .source import validate_mapping
                try:
                    validate_mapping(load(mapping),production=True)
                    if sha(mapping)!=binding['read_config']['g3t'].get('mapping_sha256'):
                        reasons.append('original mapping differs from binding')
                except ValueError as exc:reasons.append(str(exc))
    for name in ('uploaded_media_root','extra_files','config','artifact','data_receipt',
                 'label_file','media_root','proof_keys'):
        if not inputs.get(name):reasons.append('missing staged input: '+name)
    if binding['read_config']['frames']['count']!=32:
        reasons.append('Native cache/geometry contracts support 32 model anchors; dense G3T uses 64 frames')
    if binding['read_config']['g3t']['source']=='clip32' and kind!='harness':
        reasons.append('clip32 is diagnostic only; production refused')
    return reasons
