"""Closed export identities, including claimed unscheduled generations."""
import re
from pathlib import Path

NAMESPACE='8865619b'
RUNS={'359fcc3c':'x_f5c353f7','17c4ffa4':'x_3fdda0fb','469ddece':'x_07ca49df'}
STOPS=('mstop','mstopB','mstopC')

def expected(run, step, generation=None, namespace=NAMESPACE):
    if (namespace!=NAMESPACE or run not in RUNS or type(step) is not int
            or (run=='469ddece' and (step!=544 or generation!='mstop'))):
        raise ValueError('Unregistered export identity')
    if generation is None:
        if step not in (100,200):raise ValueError('Unregistered milestone')
        generation='m'+str(step)
    elif run!='469ddece' and (run!='17c4ffa4' or generation not in STOPS or not 1<=step<=200):
        raise ValueError('Unregistered stop generation')
    root='/project/community/jjyeung/okh7/'+RUNS[run]+'/o/'
    return dict(run=run,step=step,namespace=namespace,generation=generation,
        object='q8/'+namespace+'/'+run+'_'+generation+'.tar',
        done=root+'gcs_'+run+'_m'+str(step)+'.done',
        claim=root+'gcs_'+run+'_'+generation+'.claim' if generation in STOPS else None)

def validate(value):
    if not isinstance(value,dict):raise ValueError('Missing export binding')
    wanted=expected(value['run'],value['step'],
        value['generation'] if value['generation'] in STOPS else None,value['namespace'])
    if value!=wanted:raise ValueError('Export binding differs')
    return wanted

def parse(raw, value, claim=None):
    value=validate(value)
    if value['claim'] and claim!=('m'+str(value['step'])+'\n').encode():
        raise ValueError('Stop claim differs from optimizer step')
    match=re.fullmatch(re.escape(value['object']).encode()+rb' ([1-9][0-9]*) ([0-9a-f]{64})\n?',raw)
    if match is None:raise ValueError('Completion receipt identity or format differs')
    return dict(object=value['object'],bytes=int(match[1]),sha256=match[2].decode())
