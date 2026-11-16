from pathlib import Path
p=Path('kit/rebind.py');s=p.read_text().replace("        L.fetch(a.destination, transfer=lambda argv,out,err,size: governed_transfer(argv,out,err,size,c['token']))", """        def transfer(argv, out, err, size):
            try:
                governed_transfer(argv, out, err, size, c['token'])
            except Exception as error:
                raise L.TransferRegistrationRequired('Governed transfer stopped; reconcile it without retry: '+str(error)) from error
        L.fetch(a.destination, transfer=transfer)""")
p.write_text(s)
p=Path('tests/rehearse.py');s=p.read_text();needle="    (ROOT/'out'/('coverage_'+key+('_done' if '--done' in sys.argv else '')+'.json')).write_text(json.dumps({n:sorted(v) for n,v in sorted(lines.items())},indent=1)+'\\n')"
s=s.replace(needle,needle+"\n    import hashlib\n    (ROOT/'out'/('coverage_'+key+('_done' if '--done' in sys.argv else '')+'_pins.json')).write_text(json.dumps({n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in lines if Path(n).is_file()},indent=1)+'\\n')")
p.write_text(s)
