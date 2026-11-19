"""Call an unchanged native builder; explicit-token override defaults OFF."""
import argparse, os, re, runpy, sys
from pathlib import Path

def adapted(source,kind,tok,enabled=False):
    if not enabled:return source
    if not re.fullmatch('[a-f][0-9a-f]{10,15}',tok or ''):raise ValueError('Invalid explicit token')
    if kind=='d':
        old="token='d'+os.urandom(6).hex();assert not (k/('a15_cot_ap'+token)).exists()"
        new="token=%r;assert not (k/('a15_cot_ap'+token)).exists()"%tok
    else:
        old="    while True:\n        tok = os.urandom(7).hex()[:13]\n        if not (K/('a15_cot_ap'+tok)).exists() and re.fullmatch('[a-f][0-9a-f]{10,15}', tok): break"
        new="    tok = %r\n    assert not (K/('a15_cot_ap'+tok)).exists()"%tok
    if source.count(old)!=1:raise ValueError('Native token mint changed; review adapter')
    return source.replace(old,new)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--enable-token',action='store_true');p.add_argument('--token');p.add_argument('--kind',choices=('d','r10'),required=True);p.add_argument('--source',required=True);p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
    source=Path(a.source).resolve();sys.path.insert(0,str(source.parent));args=a.args[1:] if a.args[:1]==['--'] else a.args;sys.argv=[str(source)]+args
    if not a.enable_token:return runpy.run_path(str(source),run_name='__main__')
    text=adapted(source.read_text(),a.kind,a.token,True)
    exec(compile(text,str(source),'exec'),dict(__file__=str(source),__name__='__main__'))
if __name__=='__main__':main()
