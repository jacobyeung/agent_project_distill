import sys,json
for l in open(sys.argv[1]):
    if not l.startswith('{'):print(l.strip());continue
    d=json.loads(l)
    keys=('case','role','fail','ok','as_expected','expected','status','steps','refusal','entry','limit','kit_hooks','kit_tb','bound_sizes','r0','forward','forward_device','forward_wrapper','sim_driver','interop_note','guard_sha256','count_before_mask','current_device_under_mask','tensor_under_mask','available_under_mask','count_under_mask','count_after_lift','available_after_lift','initialized_before_open','dev','dev_error','imported','open_failure')
    print(json.dumps({k:d[k] for k in keys if k in d and d[k] is not None})[:2200])
    for m in d.get('marks',[]):print('   mark',json.dumps(m)[:300])
    for k in ('refusal_failure','failure','entry_failure','hook_failure','trace_failure'):
        if d.get(k):print('  ',k,json.dumps(d[k])[:1500])
    for k,v in list((d.get('cuda_calls') or {}).items())[:int(sys.argv[2]) if len(sys.argv)>2 else 30]:print('   call',v,k[:240])
