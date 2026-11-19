"""Full CPU comparison with an explicit main guard and no child processes."""
import os,sys,json,hashlib,time,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1]
from cpu_guard import install

def main(name):
    T=W/'work'/name
    install(W,'final_'+name)
    os.chdir(T);sys.path.insert(0,str(T));sys.path.extend([str(T/'generator/derivgen_v7'),str(T/'generator/ground_rows_out')])
    def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    inputs=[pin(p) for p in sorted(T.rglob('*.py')) if '/artifacts/' not in str(p)]
    inputs.extend([pin(Path(__file__).resolve()),pin(W/'scripts/cpu_guard.py')])
    class Result(unittest.TextTestResult):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.records=[]
        def addSuccess(self,t):super().addSuccess(t);self.records.append({'id':t.id(),'status':'PASS'})
        def addError(self,t,e):super().addError(t,e);self.records.append({'id':t.id(),'status':'ERROR','error':str(e[1])})
        def addFailure(self,t,e):super().addFailure(t,e);self.records.append({'id':t.id(),'status':'FAIL','error':str(e[1])})
        def addSkip(self,t,r):super().addSkip(t,r);self.records.append({'id':t.id(),'status':'SKIP','reason':r})
        def addSubTest(self,t,sub,e):
            super().addSubTest(t,sub,e)
            if e is not None:self.records.append({'id':sub.id(),'status':'FAIL' if issubclass(e[0],t.failureException) else 'ERROR','error':str(e[1])})
    start=time.monotonic();modules=sorted((T/'tests').glob('test*.py'))
    with (W/'out'/('CPU_FINAL_'+name+'.log')).open('x') as f:
        suite=unittest.TestSuite()
        for p in modules:
            module='tests.'+p.stem
            try:suite.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
            except Exception as error:suite.addTest(unittest.loader._FailedTest(module,error))
        result=unittest.TextTestRunner(stream=f,verbosity=2,resultclass=Result).run(suite)
    record={'tree':name,'modules_attempted':len(modules),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'seconds':time.monotonic()-start,'records':result.records,'failed_cases':[dict(id=t.id(),status=s,traceback=trace) for s,pairs in [('FAIL',result.failures),('ERROR',result.errors)] for t,trace in pairs],'inputs':inputs,'restrictions':'No subprocesses, multiprocessing starts, sockets, NFS access, deletion or external writes; refusals remain errors.'}
    (W/'out'/('CPU_FINAL_'+name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print({k:v for k,v in record.items() if k not in ('records','inputs','failed_cases')},flush=True)

if __name__=='__main__':main(sys.argv[1])
elif __name__=='__mp_main__':
    raise RuntimeError('CPU suite runner cannot be imported as a worker entrypoint')
