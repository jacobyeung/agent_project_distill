The tree publishes `q/host.json` and `RESULT.json.host_receipt` only after the final `bind_handover`, persisted admission, final-config loader audit, optional forward proof, and seven host assertions succeed. The kit must consume that pin. These are integration instructions; this build changes no kit files.

In `b/a.py:24–29`, retain `recorded_host` for mode p and limit its installation to p:

```python
if sys.argv[1] == 'p':
    host_entry.frame_host = recorded_host
```

Do not wrap `production_proof.run` to author a second host receipt. In q, `root/'host.json'` is not the receipt source.

In `b/h.py:16–19`, replace the receipt lookup with the exact result pin:

```python
hp = q.get('host_receipt')
if not isinstance(hp, dict) or set(hp) != {'path', 'sha256'}:
    raise ValueError('R1_HOST_RECEIPT_MISSING')
source = r/'q/host.json'
if hp['path'] != str(source.resolve()):
    raise ValueError('R1_HOST_RECEIPT_PATH_DIFFERS')
if not source.is_file() or source.is_symlink():
    raise ValueError('R1_HOST_RECEIPT_MISSING')
try:
    host = load(checked(str(source), hp['sha256']))
except (ValueError, OSError):
    raise ValueError('R1_HOST_RECEIPT_INVALID') from None
```

Keep `h.py:20–30` unchanged: validate status, exact final identity, the seven true assertions and complete loader audit; pin `hr.json`; synchronize preparation; verify identity preservation. Keep `rv.py`, `t.py` and `u.py` admission and review checks unchanged.

The q request also needs real host inputs. At `b/a.py:33–39`, supply `job_tmp=str(root/'q')`, `binaries` from decoded `k/h.json`, and authenticated `staging` and `routing_selection` pins. Keep the authenticated `routing_base` from decoded `k/r.json`. N's deferred request must not gain routing slices or a `routing_inputs` field. Every config/request absolute path must resolve inside `root/'q'`; pin paths, persisted-file destinations, model directories, frame roots and cache/output paths all count. `root/'q'` must not exist when `run` begins. Code extraction under `root/'s'` is outside this fresh job namespace.

Move payload writes from `b/z.py:449–525` (`stage_payload`) and its call at `b/z.py:602` into the tree's staging hook, invoked from `b/a.py:39`:

```python
def stage(entries, directory):
    # The merged kit supplies its authenticated copier here. It must copy the
    # already pinned bytes into directory without changing the config/request.
    copy_resolved_payload(entries, directory)

r = run(request, root/'q', stage=stage)
```

`copy_resolved_payload` above names the copier the kit merger must implement from `stage_payload`; it is not an existing kit function. The hook receives the authenticated staging manifest's `entries` and the fresh q root. The tree establishes freshness, confinement, environment and mode 0700, checks disk/binaries, authenticates the manifest and validates its coverage before calling the hook. It then runs native scene and routing checks. The default hook is `launch_r2.staging.stage_inputs`; use it directly when its payload/archive manifest represents the closure.

Split the resolver into read-only planning and copying. Before `run`, the planner must compute the exact localized config bytes, all pins and the manifest without creating q. Keep bootstrap metadata outside q and expose its authenticated pins through the existing process-local `scope` map. The config/request pins themselves use their future q paths. `verify_staging`, routing/room preflight and `begin_host` read this metadata before the hook, so all preflight metadata must be available through that map. Large inputs stay with the copier; do not embed weights in JSON.

`stage_payload` currently changes manifest/persisted paths and writes `c.json`, `n.json` and `r.json`. Compute those path bindings in the planner; the hook must publish exactly the planned bytes. Rename its staged code metadata `c.json` to `source_code.json` and rebind its references, because native q owns `q/c.json`. Preserve `q/h`, `q/p`, `q/b`, `q/a`, `q/selection`, `q/host.json` and `q/RESULT.json` for tree outputs. Route frame staging through the same fresh-namespace lifecycle. The hook must preserve all existing hash, inventory, path and archive checks.

`b/a.py:36–38` currently refreshes the pool before `run`. Perform that refresh in bootstrap scratch, localize its resulting metadata to the future q paths, authenticate the resulting config and include those bytes in the staging plan. Do not create q to refresh it, and do not change the config inside the copier after the tree has read it. Preserve `i.py`'s same-row comparison. A changed pool receipt or output path can change `digest(s1_routing.build(...))`; the independent reviewer must approve the digest for the exact runtime inputs and paths. Never substitute the routing receipt's file SHA256 for `regenerated_sha256`.

The routing pin is unresolved: `ROUTING_SELECTION_PIN.json` identifies the missing ca0616db receipt and its exact upload source. Decoded `k/h.json` still has null `staging` and `routing_selection`; copying those nulls cannot pass. The later kit build must supply these inputs, update source archive/code pins to the new tree seal, reseal the kit, and rerun kit verification, refusal and hidden-path tests. No production host PASS, launch GO or independent review is supplied here.
