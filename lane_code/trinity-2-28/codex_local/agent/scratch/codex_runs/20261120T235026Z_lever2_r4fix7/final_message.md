Fixed. The [path translator](/scratch/jjyeung/orch_n30/lever1_c/r4kit/src/storage.py:84) renamed `keyword.py` because it matched `word`. It also affected `email._encoded_words`, both `importlib` readers modules, and both SAX reader modules. D400 preserved these native paths.

[The fix](/scratch/jjyeung/orch_n30/lever1_c/r4kit/src/storage.py:108) limits renaming to authored sources. Memory guard and FROZEN.json remain unchanged.

**38 CPU tests passed**, including production-namespace imports using the staged local interpreter: 4,806 files verified and 1,170 modules loaded. [Evidence and limitations](/scratch/jjyeung/orch_n30/lever1_c/r4kit/IMPORTS.md).

Token: `f68a2d7c903be`. All four metadata files agree.

[Delivery](/scratch/jjyeung/orch_n30/lever1_c/r4kit/out/delivery.tgz): **4,252,467 bytes**  
SHA-256: `ce4667f5dca811b380a1d8d4b101e488372d4ea132746abcc1d29420cac40db7`