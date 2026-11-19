from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build20'
s=(L/'work/build17/native_assets17.py').read_text()
s=s.replace('hidden_size=8,intermediate_size=16','hidden_size=4,intermediate_size=8').replace('head_dim=4','head_dim=2')
s=s.replace('out_hidden_size=8','out_hidden_size=4').replace('mrope_section=[0,0,2]','mrope_section=[0,0,1]')
s=s.replace('vocab_size=248064,','vocab_size=248064,tie_word_embeddings=True,')
s=s.replace('cfg=Qwen3_5Config(text_config=text,','cfg=Qwen3_5Config(tie_word_embeddings=True,text_config=text,')
(B/'native_assets20.py').write_text(s)
p=B/'native20.py';s=p.read_text().replace("str(L/'work/build17'),str(L/'work/n1fix2')", "str(B),str(L/'work/build17'),str(L/'work/n1fix2')")
s=s.replace('from native_assets17 import','from native_assets20 import')
p.write_text(s)
p=B/'jobtest.py';s=p.read_text().replace('cls.run=', 'cls.run_pins=').replace('cls.run)', 'cls.run_pins)').replace('dict(cls.run,','dict(cls.run_pins,')
p.write_text(s)
