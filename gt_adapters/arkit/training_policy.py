"""Pin the teacher's request settings and recognize provider output exhaustion."""
import contextvars,os
MODEL='gemini-3.1-pro-preview'
_REQUEST=contextvars.ContextVar('r1308_request',default=None)
def normalize_finish(value):
    token=str(getattr(value,'value',value)).strip().lower().split('.')[-1]
    return 'max_tokens' if token in {'length','max_tokens','max_output_tokens'} else token
def is_capped(message):
    return normalize_finish((getattr(message,'response_metadata',{}) or {}).get('finish_reason'))=='max_tokens'
def budget_terminal(attempts):
    return any(normalize_finish(r.get('finish_reason'))=='max_tokens' and (r.get('status')=='ok' or r.get('native_output_cap_evidence')) for r in (attempts or []))
def request_controls():
    value=_REQUEST.get()
    if value is None: raise RuntimeError('planner request was not captured')
    return dict(value)
def checked_request(request):
    config=request['config'].model_dump(mode='json',exclude_none=True)
    controls={k:config[k] for k in ('temperature','max_output_tokens','thinking_config','top_p','top_k','seed') if k in config}
    controls['model']=request['model']
    expected={'model':MODEL,'temperature':0.0,'max_output_tokens':int(os.environ['REQ73_PLANNER_OUTPUT_BUDGET']),
        'thinking_config':{'include_thoughts':True,'thinking_level':'HIGH'}}
    if controls!=expected: raise RuntimeError('teacher request differs from pinned inference settings')
    _REQUEST.set(controls)
    return request
def planner_class():
    from langchain_google_genai import ChatGoogleGenerativeAI
    class TrainingPlanner(ChatGoogleGenerativeAI):
        def _prepare_request(self,*args,**kwargs):
            return checked_request(super()._prepare_request(*args,**kwargs))
    return TrainingPlanner


def native_cap_since(started_unix):
    """Recover a native cap that LangChain could not convert into an AI message."""
    from training_assets import current_archive,read_json,sha
    archive=current_archive();requests={}
    for line in archive.journal_path.read_text().splitlines():
        row=__import__('json').loads(line);path=archive.root/row['path'];event=read_json(path)
        if event['time_ns'] < int(started_unix*1e9):continue
        value=event['payload'];call=value.get('call_id')
        if event['kind']=='provider_request':requests[call]=value
        elif event['kind'] in ('provider_response','provider_chunk') and call in requests:
            request=requests[call].get('kwargs',{})
            if str(request.get('model','')).removeprefix('models/')!=MODEL:continue
            response=value.get('response') or {};usage=response.get('usage_metadata') or {}
            if any(normalize_finish(c.get('finish_reason'))=='max_tokens' for c in response.get('candidates') or []):
                if not all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_token_count','candidates_token_count','total_token_count')):continue
                return {'event_path':str(path),'event_sha256':sha(path),'call_id':call,'response':response}
    return None
