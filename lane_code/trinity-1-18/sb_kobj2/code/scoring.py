"""The exact float64 scorer registered in specification section 6."""
import numpy as np
class Scorer:
 def __call__(self,item,prediction):
  if prediction is None:return 0.
  typ=item.get('question_type',item.get('type'))
  truth=item.get('gt_released',item.get('answer',item.get('gt')))
  if typ in ('object_size_estimation','object_abs_distance','object_counting'):
   try:p,t=np.float64(prediction),np.float64(truth)
   except (ValueError,TypeError):return 0.
   if not np.isfinite(p) or not np.isfinite(t) or t<=0:return 0.
   return float(np.mean(np.abs(p-t)/t <= 1-np.linspace(.5,.95,10,dtype=np.float64)))
  return float(str(prediction).strip()==str(truth).strip())
