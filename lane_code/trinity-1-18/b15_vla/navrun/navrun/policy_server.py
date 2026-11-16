"""Synchronous JSON-lines policy worker over stdin/stdout; no sockets or background process."""
import argparse
import importlib
import json
import sys
import numpy as np
from vla_where.nav import OBS_KEYS

def serve(policy, source, destination):
    for line in source:
        try:
            request=json.loads(line)
            if set(request) != OBS_KEYS:
                raise ValueError('Policy requests need exactly the schema 8.4 fields')
            frames=[None if x is None else np.asarray(x,dtype=np.uint8) for x in request['frames']]
            state={k:request[k] for k in ('executed','decision_index','constants')}
            answer=policy.act(frames,request['instruction'],state)
            response=dict(answer=answer)
        except (ValueError,TypeError,KeyError) as error:
            response=dict(error=str(error))
        destination.write(json.dumps(response,allow_nan=False)+'\n');destination.flush()

def main():
    p=argparse.ArgumentParser();p.add_argument('--factory',required=True,help='local module:zero_argument_factory')
    a=p.parse_args();module,name=a.factory.split(':',1)
    policy=getattr(importlib.import_module(module),name)()
    serve(policy,sys.stdin,sys.stdout)
if __name__=='__main__':main()
