"""Streaming, training-only channel moments. No feature maps are persisted."""
import torch
from torch.nn import functional as F

VARIANCE_FLOOR=1e-6


class ChannelMoments:
    def __init__(self):
        self.taps=None

    def update(self,maps):
        if len(maps)!=4:raise ValueError('Four taps required for channel statistics')
        if self.taps is None:self.taps=[None]*4
        for k,m in enumerate(maps):
            x=m.detach().reshape(-1,m.shape[-1]).double()
            if not torch.isfinite(x).all():raise ValueError('Nonfinite calibration features')
            n=len(x);mean=x.mean(0);m2=((x-mean)**2).sum(0)
            old=self.taps[k]
            if old is not None:
                count,mu,ss=old;delta=mean-mu;total=count+n
                m2=ss+m2+delta.square()*count*n/total
                mean=mu+delta*n/total;n=total
            self.taps[k]=(n,mean,m2)

    def finish(self):
        if not self.taps:raise ValueError('No training calibration frames')
        return dict(variance_floor=VARIANCE_FLOOR,taps=[dict(tokens=n,mean=mean.tolist(),
            std=(m2/n).clamp_min(VARIANCE_FLOOR).sqrt().tolist()) for n,mean,m2 in self.taps])


def standardize_maps(maps,statistics):
    if len(maps)!=len(statistics['taps']):raise ValueError('Statistics tap count differs')
    output=[]
    for m,s in zip(maps,statistics['taps']):
        mean=torch.tensor(s['mean'],device=m.device,dtype=torch.float32)
        std=torch.tensor(s['std'],device=m.device,dtype=torch.float32)
        if mean.numel()!=m.shape[-1] or std.shape!=mean.shape or not torch.isfinite(mean).all() or not torch.isfinite(std).all() or (std<VARIANCE_FLOOR**.5).any():
            raise ValueError('Invalid channel statistics')
        output.append((m.float()-mean)/std)
    return output


class EnergyAudit:
    """Report the largest channel's energy share before/after standardization, after LN."""
    def __init__(self):self.values={}

    def update(self,maps,statistics,split):
        from .core import readout_maps
        for label,arrays in [('before',maps),('after',standardize_maps(maps,statistics)),
                ('before_head',readout_maps(maps,'unstandardized')),
                ('after_head',readout_maps(maps,'four',statistics))]:
            for k,m in enumerate(arrays):
                x=F.layer_norm(m.float(),(m.shape[-1],)).reshape(-1,m.shape[-1])
                energy=x.double().square();total=energy.sum(-1)
                shares=energy.max(-1).values/total.clamp_min(1e-30)
                key=(split,k,label);old=self.values.get(key)
                value=(energy.sum(0),float(shares.sum()),len(x))
                self.values[key]=value if old is None else (old[0]+value[0],old[1]+value[1],old[2]+value[2])

    def finish(self):
        rows=[]
        for (split,tap,label),(energy,share,n) in sorted(self.values.items()):
            rows.append(dict(split=split,tap=tap+1,stage=label,tokens=n,
                largest_channel=int(energy.argmax()),largest_channel_energy_share=float(energy.max()/energy.sum().clamp_min(1e-30)),
                mean_token_largest_channel_share=share/n))
        return rows
