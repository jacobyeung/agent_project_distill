from pathlib import Path
def main(k):
 (Path(k)/'verified').write_text('yes')
