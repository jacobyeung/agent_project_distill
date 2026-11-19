"""Occupancy checks and one persistent nvidia-smi telemetry process."""
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from common228 import Refusal, write, utc

def card_name(card):
    if not re.fullmatch(r'(?:[0-7]|GPU-[0-9a-fA-F-]{16,})',str(card)):
        raise Refusal('Name exactly one card, by index 0..7 or GPU UUID')
    return str(card)

def snapshot(card, run=subprocess.run):
    card_name(card)
    result=run(['nvidia-smi','-i',str(card),'-q','-x'],capture_output=True,text=True,timeout=20,check=True)
    root=ET.fromstring(result.stdout);gpus=root.findall('gpu')
    if len(gpus)!=1:raise Refusal('nvidia-smi did not resolve exactly one GPU')
    gpu=gpus[0]
    def mib(key):
        text=gpu.findtext('fb_memory_usage/'+key,'')
        match=re.fullmatch(r'\s*(\d+)\s+MiB\s*',text)
        if not match:raise Refusal('Unavailable GPU memory reading')
        return int(match[1])
    processes=gpu.find('processes')
    if processes is None:raise Refusal('nvidia-smi omitted process occupancy')
    if processes.text and processes.text.strip() not in ('','None'):
        raise Refusal('Unavailable GPU process reading')
    return dict(uuid=gpu.findtext('uuid'),name=gpu.findtext('product_name'),
        memory_used_mib=mib('used'),memory_total_mib=mib('total'),
        processes=[{x.tag:x.text for x in p} for p in processes.findall('process_info')],
        driver=root.findtext('driver_version'))

def require_idle(value):
    if not value.get('uuid') or not value.get('name'):raise Refusal('Incomplete GPU identity')
    if 'RTX 6000 Ada' not in value['name'] or not 48_000<=value['memory_total_mib']<=50_000:
        raise Refusal('Require the named RTX 6000 Ada 49 GB card')
    if value['memory_used_mib']>=100 or value['processes']:
        raise Refusal('Card is busy: require <100 MiB and no compute or graphics process')

def idle_gate(card, evidence, *, get=snapshot, sleep=time.sleep, clock=time.monotonic):
    first=get(card);require_idle(first);start=clock()
    write(evidence,dict(complete=False,first=first,wait_seconds=300,utc=utc()))
    # Small sleeps allow signals and progress messages; tests inject time, production cannot override it.
    while clock()-start<300:
        sleep(min(30,300-(clock()-start)))
    second=get(first['uuid']);require_idle(second)
    if first['uuid']!=second['uuid']:raise Refusal('GPU identity changed between idle readings')
    elapsed=clock()-start
    if elapsed<300:raise Refusal('Idle readings were less than five minutes apart')
    write(evidence,dict(complete=True,first=first,second=second,elapsed_seconds=elapsed,utc=utc()))
    return second

class Sampler:
    def __init__(self, card, destination):
        self.card=card;self.destination=destination;self.process=None
    def __enter__(self):
        self.stream=self.destination.open('xb')
        self.process=subprocess.Popen(['nvidia-smi','-i',self.card,
            '--query-gpu=timestamp,uuid,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw',
            '--format=csv','-l','1'],stdout=self.stream,stderr=subprocess.STDOUT)
        return self
    def __exit__(self,*args):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill();self.process.wait()
        self.stream.close()
