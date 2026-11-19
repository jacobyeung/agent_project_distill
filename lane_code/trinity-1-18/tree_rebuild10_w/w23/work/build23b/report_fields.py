from pathlib import Path
L=Path(__file__).resolve().parents[2];p=L/'work/build23b/finish.py';s=p.read_text()
s=s.replace('deferred rows_per_step/ceiling_rows_per_step; population counts and indices, including omitted deferred cells.', 'rows_per_step/ceiling_rows_per_step of every routing cell except routing_base; deferred population counts and indices, including omitted cells.')
s=s.replace('removal lists, wording exclusions, room authority, component evidence and staged hash inventories', 'removal lists, wording exclusions, extent receipts, room authority, component evidence and staged hash inventories')
p.write_text(s)
