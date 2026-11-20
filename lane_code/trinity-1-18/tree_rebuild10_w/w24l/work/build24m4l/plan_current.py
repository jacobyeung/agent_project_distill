from common import *
s=(D/'plan_test.py').read_text()
s=s.replace("resolved['config']=J.load(D/'candidate/qd/n.json')","resolved['config']=J.load(kit('qd')/'k/n.json')")
s=s.replace("assert plan['config']['min_pixels']==16384 and plan['config']['max_pixels']==147456", "assert plan['config'].get('min_pixels') is None and plan['config'].get('max_pixels') is None\nassert plan['config']['frame_count']==32")
s=s.replace('real N candidate','sealed C-prime N configuration')
exec(compile(s,str(D/'plan_test.py'),'exec'))
