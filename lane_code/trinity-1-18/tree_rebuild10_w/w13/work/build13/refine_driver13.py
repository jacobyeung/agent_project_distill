from pathlib import Path
p=Path(__file__).with_name('census13.py');s=p.read_text()
a=s.index('# The fixture uses');b=s.index("v=load(pinned(cfg['streams']['vqa']))")
block=s[a:b]
replacement="""if '--resume' in sys.argv:
    composed=load(O/'composed/receipt.json')
    slice_counts=load(O/'slice_intake.json')
    con=sqlite3.connect((O/'base.sqlite').as_uri()+'?mode=ro',uri=True)
    camera={family(json.loads(r),'routing'):json.loads(r) for (r,) in con.execute('SELECT row FROM rows')}
    con.close()
else:
"""+''.join('    '+line if line.strip() else line for line in block.splitlines(True))
s=s[:a]+replacement+s[b:]
a=s.index('refused=Counter();indices=[];bycell=Counter()');b=s.index("reader.indices['vqa']=indices")
block=s[a:b]
replacement="""if '--resume' in sys.argv:
    prior=load(O/'CENSUS.json')['vqa'];pinned(prior['database'])
    indices=load(O/'vqa_indices.json');bycell=Counter(prior['eligible_by_cell']);refused=Counter(prior['refused'])
    assert dict(bycell)==expected['streams']['vqa']['eligible_by_cell']
else:
"""+''.join('    '+line if line.strip() else line for line in block.splitlines(True))
s=s[:a]+replacement+s[b:]
p.write_text(s)
