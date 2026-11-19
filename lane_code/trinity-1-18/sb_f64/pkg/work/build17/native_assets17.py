"""Permitted fixture boundaries: tiny model and HF processor constructor."""
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch


class PatchGridProcessor:
    """CPU RGB patchification with the native HF tensor schema and patch counts.

    Replaces AutoProcessor's image/video constructor, which needs torchvision.
    The tokenizer is a real persisted HF tokenizer. Each temporal pair produces
    four 2x2 RGB patches and one merged video token, as the tiny vision config
    specifies. Native RGB loading, prompt/target masking and model forward run.
    """
    def __init__(self, root):
        from transformers import PreTrainedTokenizerFast
        self.tokenizer=PreTrainedTokenizerFast.from_pretrained(root,local_files_only=True)
        self.video_token_id=self.tokenizer.convert_tokens_to_ids('<|video_pad|>')
        self.video_processor=SimpleNamespace(merge_size=2,temporal_patch_size=2,
            image_mean=[.5]*3,image_std=[.5]*3)
        self.image_processor=SimpleNamespace(merge_size=2,patch_size=2)

    def apply_chat_template(self,messages,**kwargs):
        prompt='<|im_start|>user\n<video>'+messages[0]['content'][1]['text']+'<|im_end|>\n<|im_start|>assistant\n'
        return prompt if len(messages)==1 else prompt+messages[-1]['content']+'<|im_end|>\n'

    def __call__(self,text,videos=None,video_metadata=None,images=None,**kwargs):
        arrays=np.asarray(videos[0] if videos is not None else images)
        if arrays.ndim==3:arrays=arrays[None]
        if len(arrays)%2:arrays=np.repeat(arrays,2,axis=0)
        # Nearest sampling is the declared constructor stand-in's resize rule.
        iy=np.linspace(0,arrays.shape[1]-1,4).astype(int)
        ix=np.linspace(0,arrays.shape[2]-1,4).astype(int)
        pixels=arrays[:,iy][:,:,ix].astype('float32')/127.5-1
        groups=len(pixels)//2
        patches=pixels.reshape(groups,2,2,2,2,2,3).transpose(0,2,4,6,1,3,5).reshape(-1,24)
        meta=video_metadata[0] if video_metadata else None
        visual=''
        for i in range(groups):
            stamp=sum(meta.frames_indices[2*i:2*i+2])/(2*meta.fps) if meta else 0
            visual+=f'<{stamp:.1f} seconds><|vision_start|><|video_pad|><|vision_end|>'
        value=text[0].replace('<video>',visual)
        ids=torch.tensor([self.tokenizer.encode(value,add_special_tokens=False)])
        return dict(input_ids=ids,attention_mask=torch.ones_like(ids),
            mm_token_type_ids=torch.where(ids==self.video_token_id,2,0),
            video_grid_thw=torch.tensor([[groups,2,2]]),pixel_values_videos=torch.tensor(patches))


def assets(root):
    from tokenizers import Tokenizer,models,pre_tokenizers,decoders
    from transformers import PreTrainedTokenizerFast,Qwen3_5Config,Qwen3_5ForConditionalGeneration
    from student_pilot.p3_provenance import file_pin
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    special={'<unk>':0,'<pad>':1,'<|fim_middle|>':2,'<|endoftext|>':248044,
        '<|im_start|>':248045,'<|im_end|>':248046,'<|vision_start|>':248047,
        '<|vision_end|>':248048,'<|video_pad|>':248049,'<|image_pad|>':248050}
    vocab={x:i+100 for i,x in enumerate(sorted(pre_tokenizers.ByteLevel.alphabet()))}
    vocab.update(special)
    used=set(vocab.values())
    vocab.update({f'<r{i}>':i for i in range(248051) if i not in used})
    tk=Tokenizer(models.BPE(vocab=vocab,merges=[],unk_token='<unk>'))
    tk.pre_tokenizer=pre_tokenizers.ByteLevel(add_prefix_space=False)
    tk.decoder=decoders.ByteLevel()
    tokenizer=PreTrainedTokenizerFast(tokenizer_object=tk,unk_token='<unk>',pad_token='<pad>',
        eos_token='<|im_end|>',additional_special_tokens=list(special))
    tokenizer.save_pretrained(root)
    text=dict(vocab_size=248064,hidden_size=8,intermediate_size=16,num_hidden_layers=2,
        num_attention_heads=2,num_key_value_heads=1,head_dim=4,use_cache=False,
        layer_types=['linear_attention','full_attention'],linear_key_head_dim=2,
        linear_value_head_dim=2,linear_num_key_heads=2,linear_num_value_heads=2,pad_token_id=1,
        rope_parameters=dict(rope_type='default',rope_theta=10000.,mrope_section=[0,0,2],partial_rotary_factor=1.))
    vision=dict(depth=3,hidden_size=8,intermediate_size=16,num_heads=2,out_hidden_size=8,
        num_position_embeddings=16,patch_size=2,temporal_patch_size=2,spatial_merge_size=2)
    cfg=Qwen3_5Config(text_config=text,vision_config=vision,image_token_id=248050,
        video_token_id=248049,vision_start_token_id=248047,vision_end_token_id=248048)
    for obj in (cfg,cfg.text_config,cfg.vision_config):obj._attn_implementation='sdpa'
    torch.manual_seed(31)
    model=Qwen3_5ForConditionalGeneration(cfg)
    model.save_pretrained(root)
    return model
