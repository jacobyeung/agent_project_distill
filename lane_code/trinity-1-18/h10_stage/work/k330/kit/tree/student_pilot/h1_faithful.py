"""S1: faithful camera labels from the existing renderer's printed own values."""
import copy
import re
import torch
from . import carrier_c1_routing as routing
from generator.derivgen_v7.derivgen.materialize import materialize, MaterializeRefusal
CAMERA_TYPES = routing.CAMERA_MOTION


def validate(cfg):
    h = cfg.get('h1', {})
    flag = h.get('faithful_own_camera_rows', False)
    if type(flag) is not bool:
        raise ValueError('h1.faithful_own_camera_rows must be boolean')
    if flag:
        if tuple(h.get('camera_types', CAMERA_TYPES)) != CAMERA_TYPES:
            raise ValueError('S1 requires the three canonical camera types')
        schedule = cfg['scheduled_sampling']
        if schedule['max_own_probability'] != .5 or schedule['force_from_step'] != 1:
            raise ValueError('S1 requires max_own_probability=0.5 and force_from_step=1')


def camera(row, settings):
    return row.get('question_type') in settings.get('camera_types', CAMERA_TYPES)


def canonical_row(row):
    """Restore materializer metadata omitted by the sealed C1 row packing.

    v3.11 single-call camera programs have no frame-pair selection program. Their
    declared frame-gap rule can be reconstructed without changing the call.
    Other programs retain their metadata and fail closed in materialize.
    """
    raw = copy.deepcopy(row.get('routing', row))
    if 'routing' in row:
        raw.update(question=row['student_input']['question'],
                   options=row['student_input'].get('options') or [], target=row['target'])
    if raw.get('trace_revision') == '3.11' and raw.get('question_type') in CAMERA_TYPES:
        calls = [e for e in raw['events'] if e['kind'] == 'tool_call']
        if len(calls) == 1 and calls[0]['name'] in ('move', 'turn'):
            raw.setdefault('frame_pair_rule', 'frame_gap')
            raw.setdefault('frame_pair_turn', [])
            if raw['question_type'] == 'camera_movement_direction':
                # The packed row omits these deterministic GT printed-value margins.
                from decimal import Decimal, localcontext, Context
                event = next(e for e in raw['events'] if e['kind'] == 'tool_response')
                dx, _, dz = map(lambda x: Decimal(str(x)), event['values'][event['call_id']+'.delta']['value'])
                scores = dict(left=-dx, right=dx, forward=dz, backward=-dz)
                labels = [re.sub(r'^[A-Z][.)]\s*', '', o).lower() for o in raw['options']]
                with localcontext(Context(prec=1024)):
                    top, second = sorted((scores[o] for o in labels), reverse=True)[:2]
                    if top > 0:
                        raw.setdefault('margin_m', float(top-second))
                        raw.setdefault('margin_rel', float((top-second)/top))
    return raw


def printed_camera(row, target, spans):
    """Parse exactly the rounded response text emitted by the existing renderer."""
    responses = {e['call_id']: e for e in row['events'] if e['kind'] == 'tool_response'}
    printed = {}
    number = r'([+-]?\d+(?:\.\d+)?)'
    for span in spans:
        cid = span['call_id']; name = responses[cid]['name']
        text = target[span['start']:span['end']]
        text = text.removeprefix('<tool_response>').removesuffix('</tool_response>')
        if name == 'move':
            m = re.fullmatch(r'dx = '+number+r' m, dy = '+number+r' m, dz = '+number+r' m, distance = '+number+' m', text)
            if m is None:
                raise MaterializeRefusal('invalid_printed_move')
            values = list(map(float, m.groups()))
            printed[cid] = dict(delta=values[:3], distance=values[3])
        elif name == 'turn':
            m = re.fullmatch(r'turn = ([+-]?\d+) deg', text)
            if m is None:
                raise MaterializeRefusal('invalid_printed_turn')
            printed[cid] = dict(value=int(m[1]))
        else:
            raise MaterializeRefusal('non_camera_head')
    return printed


def faithful(row, geometry):
    raw = canonical_row(row)
    target, spans, _ = routing.rerender(raw, geometry)
    result = materialize(raw, printed_camera(raw, target, spans))
    target, spans, segments = routing.render_full(result['events'], result['answer'])
    if target != result['target']:
        raise MaterializeRefusal('faithful_render_mismatch')
    return result, target, spans, segments


def answer_differs(kind, own, gt):
    """Registered stop metric; faithful training text remains unchanged."""
    from decimal import Decimal
    if kind == 'camera_movement_direction':
        return str(own).strip() != str(gt).strip()
    a,b=Decimal(str(own)),Decimal(str(gt))
    if not a.is_finite() or not b.is_finite():raise ValueError('Nonfinite camera answer')
    if kind == 'camera_displacement':return abs(a-b) > Decimal('.1')*abs(b)
    if kind == 'camera_rotation':
        delta=(a-b+180)%360
        if delta<0:delta+=360
        return abs(delta-180)>10
    raise ValueError('Unknown camera answer type')


ROW_FAILURES = (MaterializeRefusal, routing.RenderError, ValueError, KeyError, StopIteration, IndexError)


def own_values(model, rows, batch, audit, index, decision, device):
    """Join readout and failure collectives, then train GT on a refused row."""
    from .carrier_c1_run import move
    import torch.distributed as dist
    info=dict(type='unknown',values='gt',refused=None,answer_differs=False)
    audit={**audit,'h1':info};failure=None;row=None;changed={};new=batch
    try:
        row,_=rows.row('routing',index)
        raw=row['routing'];info['type']=raw.get('question_type','unknown')
    except ROW_FAILURES as exc:
        failure=exc
    if any(decision):
        # All ranks enter this forward, even when their local metadata failed.
        uv,slots=routing.query_tensor([])
        with torch.no_grad():
            readout=model(move(routing.prefix_batch(batch),device),{'uv':uv.to(device)},stream='readout')
        try:
            if failure is not None:raise failure
            if camera(raw,rows.h1) and decision[1]:
                geometry,source=routing.row_geometry(raw,readout,[],slots,False,True)
                if geometry is None:raise routing.RenderError(source)
                result,target,spans,segments=faithful(row,geometry)
                new,changed=routing.encode_own(rows.processor,row,batch,target,spans,segments,source,faithful=True)
                differs=answer_differs(info['type'],result['answer'],raw['answer'])
                info.update(values='own',answer_differs=differs,answer=result['answer'])
        except ROW_FAILURES as exc:
            failure=exc;new=batch;changed={}
    if failure is not None:
        info.update(values='gt',answer_differs=False,
                    refused=str(getattr(failure,'reason',None) or type(failure).__name__+': '+str(failure))[:200])
    flag=torch.tensor([failure is not None],dtype=torch.int32,device=device)
    if dist.is_initialized():dist.all_reduce(flag,op=dist.ReduceOp.MAX)
    # The flag is global, the fallback is row-local. Every rank continues to backward.
    info['any_rank_refused']=bool(flag.item())
    return new,{**audit,**changed,**({'own_refusal':info['refused']} if failure is not None else {})}


def identity_check(rows):
    """Check exact GT materialization on camera rows; count every camera refusal."""
    from collections import Counter
    counts=Counter();by_type={};refusals=Counter()
    for source in rows:
        raw=source.get('routing',source)
        kind=raw.get('question_type',raw.get('type','unknown'))
        if kind not in CAMERA_TYPES:continue
        counts['rows']+=1;d=by_type.setdefault(kind,Counter());d['rows']+=1
        try:
            row=canonical_row(source)
            printed={e['call_id']:e for e in row.get('events',[]) if e['kind']=='tool_response'}
            key='identical' if materialize(row,printed)['target']==row['target'] else 'different'
            counts[key]+=1;d[key]+=1
        except ROW_FAILURES as exc:
            counts['refused']+=1;d['refused']+=1
            refusals[str(getattr(exc,'reason',None) or type(exc).__name__+': '+str(exc))]+=1
    rate=counts['identical']/counts['rows'] if counts['rows'] else None
    return dict(rows=counts['rows'],identical=counts['identical'],different=counts['different'],
                refused=counts['refused'],identity_rate=rate,refusal_reasons=dict(refusals),
                by_type=by_type,threshold=.95,passes=rate is not None and rate>=.95)


def identity_rows(path):
    """Stream JSONL rows, JSON receipts, or a read-only SQLite rows table."""
    import json
    import sqlite3
    from pathlib import Path
    from .p3_provenance import pinned
    path=Path(path).resolve()
    with path.open('rb') as handle:header=handle.read(16)
    if header==b'SQLite format 3\x00':
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as conn:
            for (text,) in conn.execute('SELECT row FROM rows ORDER BY i'):yield json.loads(text)
    elif path.suffix=='.json':
        value=json.loads(path.read_text())
        if isinstance(value,list):yield from value
        elif 'database' in value:
            yield from identity_rows(pinned(value['database']))
        elif 'streams' in value:
            source=value['streams']['routing']
            yield from identity_rows(pinned(source.get('receipt',source.get('database'))))
        else:yield value
    else:
        with path.open() as handle:
            for text in handle:
                if text.strip():yield json.loads(text)


def prepare_identity(receipt,cfg):
    """Bind S1 admission to the config's authenticated routing receipt."""
    from pathlib import Path
    from .p3_provenance import pinned,write
    if not cfg.get('h1',{}).get('faithful_own_camera_rows'):return receipt
    source=cfg['streams']['routing']
    report=dict(identity_check(identity_rows(pinned(source))),source_receipt=source)
    result={**receipt,'h1_faithful_identity':report}
    # Successful preparation writes its complete receipt in the caller.
    # A refusal leaves the measured rate and histogram before aborting.
    if not report['passes']:
        write(Path(cfg['preparation_output'])/'receipt.json',result)
    require_identity(result,cfg)
    return result


def require_identity(receipt,cfg):
    if not cfg.get('h1',{}).get('faithful_own_camera_rows'):return
    report=receipt.get('h1_faithful_identity',{})
    rate=report.get('identity_rate')
    if (report.get('source_receipt')!=cfg['streams']['routing'] or
            not report.get('rows') or rate is None or rate<.95 or not report.get('passes')):
        raise ValueError('S1 launch requires faithful identity >= 95% on the bound routing receipt')
