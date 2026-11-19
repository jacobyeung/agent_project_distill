"""Verify default byte identity and optional explicit tokens; no remote calls."""
import argparse
import ast
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import pack as P


def configured(base,root,builder):
    c=copy.deepcopy(base);c['workspace']=str(root)
    c['builder']['path']=str(builder);c['builder']['sha256']=P.file_sha(builder)
    c['builder']['args'][0]=str(root/'stage')
    c['builder']['report']=str(root/'stage/BUILD.json')
    c['builder']['env']={'KROOT':str(root/'k')}
    return c


def default_delivery(c):
    root=P.state(c);root.mkdir(parents=True,exist_ok=False)
    args=c['builder']['args'];path=Path(c['builder']['path'])
    # Deterministic entropy is a test fixture applied identically to both builds.
    # A stale requested token must do nothing while the explicit switch is off.
    code=('import os,runpy,sys;from pathlib import Path;'
          'p=Path(sys.argv[1]);sys.path.insert(0,str(p.parent));'
          'os.urandom=lambda n:bytes([n])*n;sys.argv=sys.argv[1:];'
          'runpy.run_path(str(p),run_name="__main__")')
    env=P.clean_env(root);env.update(c['builder']['env']);env['SO_PACK_TOKEN']='a0123456789ab'
    P.run([c['python'],'-I','-s','-B','-c',code,str(path)]+args,
          root,root/'build.log',env=env)
    r=P.read(c['builder']['report'])['D'];delivery=Path(r['delivery_dir'])/'1.tgz'
    P.require(P.file_sha(delivery)==r['delivery_sha256'],'Test delivery hash differs')
    return delivery.read_bytes(),r


def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True)
    p.add_argument('--baseline-config',required=True)
    p.add_argument('--patched-d',required=True);p.add_argument('--original-r10',required=True)
    p.add_argument('--patched-r10',required=True);a=p.parse_args()
    P.limit_resources();root=Path(a.work).resolve();root.mkdir(parents=True,exist_ok=False)
    base=P.read(a.baseline_config);original=Path(base['builder']['path']).resolve();patched=Path(a.patched_d).resolve()
    before={str(p):P.file_sha(p) for p in (original,Path(a.original_r10))}
    old,ro=default_delivery(configured(base,root/'a0',original))
    new,rn=default_delivery(configured(base,root/'a1',patched))
    P.require(old==new,'Default builder output changed')
    print('D_DEFAULT_BYTES_IDENTICAL_PASS sha256='+P.sha(old)+' bytes='+str(len(old)),flush=True)
    c=configured(base,root/'a2',patched);c['builder']['explicit_token_switch']=True
    tok='a0123456789ab';b=P.build(c,explicit_token=tok)
    P.require(b['report']['token']==tok,'Explicit D token differs')
    P.structure(b['package'])
    print('D_EXPLICIT_TOKEN_PASS '+tok,flush=True)
    # r10's authenticated source archives are absent. Check the exact default
    # mint loop's AST and execute only the opt-in mint branch, without imports
    # or top-level builder I/O. This is not a full r10 build claim.
    old_tree=ast.parse(Path(a.original_r10).read_text());new_tree=ast.parse(Path(a.patched_r10).read_text())
    old_loop=next(n for n in ast.walk(old_tree) if isinstance(n,ast.While))
    branch=next(n for n in ast.walk(new_tree) if isinstance(n,ast.If)
                and 'SO_PACK_EXPLICIT_TOKEN' in ast.unparse(n.test))
    P.require(len(branch.orelse)==1 and ast.dump(old_loop)==ast.dump(branch.orelse[0]),
              'r10 default mint loop changed')
    print('R10_DEFAULT_LOOP_AST_IDENTICAL_PASS',flush=True)
    os.environ.update(SO_PACK_EXPLICIT_TOKEN='1',SO_PACK_TOKEN=tok)
    ns={'os':os,'re':re,'sys':sys,'K':root/'k'}
    mod=ast.Module(body=[branch],type_ignores=[]);ast.fix_missing_locations(mod)
    saved=sys.argv[:];sys.argv=['build_r10.py',str(root),'A']
    try:
        exec(compile(mod,'mint_fixture','exec'),ns)
        P.require(ns['tok']==tok,'r10 explicit mint differs')
        sys.argv[2]='A,B'
        try:exec(compile(mod,'mint_fixture','exec'),ns)
        except AssertionError:pass
        else:raise P.GateError('r10 accepted one explicit token for two packages')
        sys.argv[2]='A';os.environ['SO_PACK_TOKEN']='bad;token'
        try:exec(compile(mod,'mint_fixture','exec'),ns)
        except AssertionError:pass
        else:raise P.GateError('r10 accepted invalid explicit token')
    finally:sys.argv=saved
    print('R10_EXPLICIT_MINT_AND_REJECTIONS_PASS (full source archives absent)',flush=True)
    P.require(before=={p:P.file_sha(p) for p in before},'Original builder source changed')
    P.write(root/'RESULTS.json',dict(passed=True,utc=P.utc(),default_delivery_sha256=P.sha(old),
        default_delivery_bytes_measured=len(old),explicit_token=tok,
        d_default_full_bytes_equal=True,d_explicit_full_build=True,
        r10_default_loop_ast_equal=True,r10_explicit_mint_only=True,
        r10_full_build=False,source_files_unchanged=before))


if __name__=='__main__':main()
