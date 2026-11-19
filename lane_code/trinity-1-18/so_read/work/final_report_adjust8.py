from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
p=L/'work/write_report8.py';s=p.read_text().replace('CUDA hidden and nice 10.',"CUDA hidden and `nice -n 10` (benchmark effective nice {cost['nice']}).")
s=s.replace('it executes the approved Python with nice 10 and','it executes the approved Python through `nice -n 10` and')
s=s.replace("('bash work/cpu.sh work/docs_check8.py','docs8.txt'),", "('bash work/cpu.sh work/docs_check8.py','docs8.txt'),('bash work/cpu.sh work/verify_archive_command8.py','archive_command8.txt'),")
p.write_text(s)
p=L/'work/integrity8.py';s=p.read_text().replace("'gate_integration8.txt','docs8.txt','storage8.txt'", "'gate_integration8.txt','docs8.txt','archive_command8.txt','storage8.txt'");p.write_text(s)
print('Final report includes archive command admission and measured effective CPU priority.')
