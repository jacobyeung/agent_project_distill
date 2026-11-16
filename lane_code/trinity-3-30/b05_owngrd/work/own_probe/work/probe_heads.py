"""Small frozen-feature probe heads; none owns encoder parameters."""
import torch
from torch import nn
from torch.nn import functional as F


class Selector(nn.Module):
    def __init__(self,feature_dim,name_dim=4096,dim=256):
        super().__init__()
        self.region=nn.Linear(feature_dim,dim)
        self.name=nn.Linear(name_dim,dim)
        self.mlp=nn.Sequential(nn.Linear(dim,dim),nn.GELU(),nn.Linear(dim,1))
    def forward(self,features,names):
        return self.mlp(F.normalize(self.region(features),dim=-1)*F.normalize(self.name(names),dim=-1)).squeeze(-1)


def listwise_loss(logits,positive,negative_weights=None):
    positive=positive.bool()
    if not positive.any():raise ValueError('Listwise group needs a positive instance')
    denominator=logits
    if negative_weights is not None:
        weights=torch.where(positive,torch.ones_like(logits),negative_weights.to(logits))
        if (weights<=0).any():raise ValueError('Listwise weights must be positive')
        denominator=logits+weights.log()
    return torch.logsumexp(denominator,dim=-1)-torch.logsumexp(logits.masked_fill(~positive,-torch.inf),dim=-1)


class ScoreFusion(nn.Module):
    def __init__(self):super().__init__();self.linear=nn.Linear(2,1)
    def forward(self,feature_logits,sam_score):
        return self.linear(torch.stack([feature_logits,torch.logit(sam_score.clamp(1e-5,1-1e-5))],-1)).squeeze(-1)


class CrossBlock(nn.Module):
    def __init__(self,dim=256):
        super().__init__();self.attn=nn.MultiheadAttention(dim,8,batch_first=True)
        self.n1=nn.LayerNorm(dim);self.n2=nn.LayerNorm(dim)
        self.ff=nn.Sequential(nn.Linear(dim,4*dim),nn.GELU(),nn.Linear(4*dim,dim))
    def forward(self,q,memory):
        q=q+self.attn(self.n1(q),memory,memory,need_weights=False)[0]
        return q+self.ff(self.n2(q))


def positional_grid(h,w,dim,device):
    yy,xx=torch.meshgrid(torch.linspace(-1,1,h,device=device),torch.linspace(-1,1,w,device=device),indexing='ij')
    freq=torch.exp(torch.arange(dim//4,device=device)*(-9.21/max(1,dim//4-1)))
    return torch.cat([(xx[...,None]*freq).sin(),(xx[...,None]*freq).cos(),
                      (yy[...,None]*freq).sin(),(yy[...,None]*freq).cos()],-1)


class MaskProbe(nn.Module):
    def __init__(self,feature_dim,name_dim=4096,dim=256):
        super().__init__();self.memory=nn.Linear(feature_dim,dim);self.query=nn.Linear(name_dim,dim)
        self.blocks=nn.ModuleList([CrossBlock(dim),CrossBlock(dim)])
        self.mask=nn.Linear(dim,dim);self.bias=nn.Parameter(torch.zeros(()))
    def forward(self,features,names,output_hw):
        n,h,w,c=features.shape
        spatial=self.memory(features)+positional_grid(h,w,self.memory.out_features,features.device)
        memory=spatial.flatten(1,2);q=self.query(names)[:,None]
        for block in self.blocks:q=block(q,memory)
        logit=torch.einsum('nc,nhwc->nhw',self.mask(q[:,0]),spatial)/(spatial.shape[-1]**.5)+self.bias
        return F.interpolate(logit[:,None],size=output_hw,mode='bilinear',align_corners=False)[:,0]


class PresenceProbe(nn.Module):
    def __init__(self,feature_dim,name_dim=4096,dim=256):
        super().__init__();self.memory=nn.Linear(feature_dim,dim);self.name=nn.Linear(name_dim,dim)
        self.score=nn.Linear(dim,1)
    def forward(self,features,names):
        memory=self.memory(features).flatten(1,2);query=self.name(names)
        weights=torch.einsum('nld,nd->nl',memory,query)/(memory.shape[-1]**.5)
        pooled=torch.einsum('nl,nld->nd',weights.softmax(-1),memory)
        return self.score(pooled*query).squeeze(-1)


class IdentityProbe(nn.Module):
    def __init__(self,feature_dim):super().__init__();self.projection=nn.Linear(feature_dim,256,bias=False)
    def forward(self,x):return F.normalize(self.projection(x),dim=-1)


def contrastive_loss(z,ids,slots,minimum_gap=8,temperature=.1):
    same=ids[:,None].eq(ids[None]);gap=(slots[:,None]-slots[None]).abs()>=minimum_gap
    valid=gap & ~torch.eye(len(z),dtype=torch.bool,device=z.device)
    positive=same&valid;eligible=positive.any(1)
    if not eligible.any():return z.sum()*0
    logits=(z@z.T/temperature)[eligible]
    denom=torch.logsumexp(logits.masked_fill(~valid[eligible],-torch.inf),1)
    numer=torch.logsumexp(logits.masked_fill(~positive[eligible],-torch.inf),1)
    return (denom-numer).mean()


def parameter_gate(model):
    count=sum(p.numel() for p in model.parameters())
    if count>=6_000_000:raise ValueError(f'Probe exceeds 6M parameters: {count}')
    return count
