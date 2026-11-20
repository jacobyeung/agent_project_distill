import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
from transformers import Qwen2TokenizerFast,CLIPProcessor,CLIPImageProcessorPil,AutoProcessor
from tokenizers.pre_tokenizers import ByteLevel
root=D/'assets2';root.mkdir()
vocab={s:i for i,s in enumerate(sorted(ByteLevel.alphabet()))}
for i in range(len(vocab),248044):vocab['<f'+str(i)+'>']=i
vocab.update({'<|endoftext|>':248044,'<|im_start|>':248045,'<|im_end|>':248046})
tok=Qwen2TokenizerFast(vocab=vocab,merges=[],eos_token='<|im_end|>',unk_token='<|endoftext|>',pad_token='<|endoftext|>')
template="{{ 'user\\n' + messages[0]['content'][1]['text'] + '\\nassistant\\n' }}{% if not add_generation_prompt %}{{ messages[-1]['content'] + '<|im_end|>\\n' }}{% endif %}"
proc=CLIPProcessor(image_processor=CLIPImageProcessorPil(),tokenizer=tok,chat_template=template)
proc.save_pretrained(root)
write(root/'config.json',dict(model_type='clip'))
p=AutoProcessor.from_pretrained(root,local_files_only=True,trust_remote_code=False)
print(type(p).__name__,p.tokenizer.eos_token_id,p.tokenizer.encode('<|endoftext|>'))
print([(f.name,f.stat().st_size) for f in root.iterdir()]);assert p.tokenizer.eos_token_id==248046
