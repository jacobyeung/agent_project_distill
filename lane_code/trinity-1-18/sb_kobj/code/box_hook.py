"""The single sibling-box binding; rule selection remains entirely in sb_kbox."""
from common import *
KBOX_RULES_HOOK=ROOT/'config/KBOX_RULES_HOOK.json'

def load(require_object=False):
 cfg=js(KBOX_RULES_HOOK)
 if cfg['status']!='BOUND':
  if require_object:raise Missing(str(KBOX_RULES_HOOK)+' (unbound sb_kbox winner/screens)')
  return None,dict(object_exists=False,size_screen=False,first_seen_screen=False)
 receipt=js(cfg['receipt_path']);assert PINS[str(local(cfg['receipt_path']))]==cfg['receipt_sha256']
 for p,h in receipt['input_sha256'].items():
  if p.startswith('/scratch') and Path(p).is_file():assert sha(p)==h
 assert sha(cfg['module_path'])==cfg['module_sha256'];m=module(cfg['module_path'],'kbox_rules_bound')
 gate=dict(object_exists=receipt['replace_box']=='PASS',size_screen=receipt['size_screen']=='PASS',first_seen_screen=receipt['first_seen_screen']=='PASS',rule=receipt.get('winning_fusion'))
 if require_object and not gate['object_exists']:raise Missing('sb_kbox first bar did not PASS')
 return m,gate
