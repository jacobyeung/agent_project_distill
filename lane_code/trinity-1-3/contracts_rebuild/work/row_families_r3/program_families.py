"""Native point-program families over a deterministic, calibrated synthetic scene."""
from derivgen.bindings import FAMILIES,NUMERIC
from derivgen.program import Program
from derivgen.common import digest
from scipy.spatial.transform import Rotation

class TemplateFixture:
    def __init__(self,plan):self.plan=plan
    def parse_vsi(self,q):return copy.deepcopy(self.plan)
    def parse_vsti(self,q):return copy.deepcopy(self.plan)
    def option_texts(self,options):return {s.split('.',1)[0]:s.split('.',1)[1].strip() for s in options}
    def letter_of(self,options,value):return next((k for k,v in self.option_texts(options).items() if v.lower()==str(value).lower()),None)
    def direction_label(self,t,a):return ('front-' if abs(a)<90 else 'back-')+('left' if a>0 else 'right') if t.endswith('hard') else 'back' if t.endswith('medium') and abs(a)>=135 else 'left' if a>0 else 'right'

class PointScene:
    """A small GT raster, pinhole readout and semantic masks; no learned model."""
    anchors=[2,4,6]
    def __init__(self,index):
        self.index=index
        self.entry=dict(infrastructure_only=True,gt=dict(path='synthetic-pinhole',sha256='a'*64),frame_indices=list(range(32)),canonical='scannet/r6_fixture_00')
        inst=np.zeros((32,64,64),int)
        for iid,x,y,start in [(1,12,28,0),(2,43,20,2),(3,28,40,4),(4,1,1,0)]:inst[start:,y:y+12,x:x+12]=iid
        self.gt=NS(inst=inst,labels=['chair','table','plant','floor'],ids=np.array([1,2,3,4]),W=64,H=64,has=lambda k:True,px=lambda uv:(np.minimum(63,np.array(uv)[:,0]*64//1000).astype(int),np.minimum(63,np.array(uv)[:,1]*64//1000).astype(int)))
        self.gt.cam=lambda k:(np.array([[1.,0,0],[0,0,1],[0,-1,0]])@Rotation.from_euler('y',k*.7,degrees=True).as_matrix(),np.array([.01*k,.05*k,0.]))
        self.ground=NS(masks=lambda name,k:[(iid,self.gt.inst[k-1]==iid) for iid in self.ids(name) if np.any(self.gt.inst[k-1]==iid)],interior=lambda m:[(np.where(m)[1].mean()+.5)/64*1000,(np.where(m)[0].mean()+.5)/64*1000])
        self.programs=NS(MIN_PX=1,closest_sets=lambda a,b:float(np.linalg.norm(a[:,None]-b[None,:],axis=-1).min()))
    def ids(self,name,many=False):return [self.gt.labels.index(name)+1]
    def appearance_masks(self,name,k):return self.ground.masks(name,k)
    def pose(self,k):
        r=Rotation.from_euler('y',k*.7,degrees=True).as_matrix()
        return dict(camera_R_L1=r,camera_t_L1=np.array([.01*k,0.,.05*k]),level_R_L1=r,yaw_degree=round(-k*.7))
    def select(self,iid,k,kind='middle',other=None):
        x,y={1:(280,530),2:(760,400),3:(530,730),4:(120,120)}[iid]
        width={1:30,2:65,3:40,4:30}[iid]
        return [[x-width,y-30],[x+width,y+30],[x,y]]
    def readout(self,iid,k,uv):
        depth={1:2.,2:2.6,3:4.,4:2.}[iid]+self.index*.03
        if iid==4:depth=1./(uv[1]/500-1)
        return dict(camera=np.array([(uv[0]/500-1)*depth,(1-uv[1]/500)*depth,depth]),spread=0.)

def program_spec(t):
    p=dict(full_referents_reviewed=True)
    opts=[]
    if t in ('object_counting','absolute_count'):p.update(cat='chair')
    elif t=='relative_count':p.update(a='chair',b='table');opts=['more','fewer','equal number']
    elif t in ('object_abs_distance','absolute_distance_object'):p.update(a='chair',b='table')
    elif t in ('object_size_estimation','absolute_size_object'):p.update(a='chair')
    elif t=='relative_size_object':p.update(a='chair',b='table',comparison='longer');opts=['chair','table']
    elif t in ('object_rel_distance','relative_distance_object'):p.update(target='chair',cands=['table','plant']);opts=['table','plant']
    elif 'direction' in t and not t.startswith('camera'):
        p.update(stand='chair',face='table',query='plant')
        opts=[] if t=='absolute_direction_object' else ['front-left','front-right','back-left','back-right'] if t.endswith('hard') else ['left','right','back'] if t.endswith('medium') else ['left','right']
    elif t=='route_planning':p.update(start='chair',face='table',plan=[('turn',None),('go','plant')]);opts=['Turn Left','Turn Right','Turn Back']
    elif t=='obj_appearance_order':p.update(cats=['chair','table','plant']);opts=['chair, table, plant','plant, table, chair']
    elif t in ('camera_displacement','camera_movement_direction','camera_rotation'):
        p.update(i=2,j=12,M=32)
        if t=='camera_movement_direction':opts=['left','right','forward','backward']
    elif t=='camera_obj_abs_dist':p.update(k=6,obj='chair')
    elif t.startswith('camera_obj_rel_dist'):p.update(k=6,cands=['chair','table']);opts=['chair','table']
    elif t.startswith('obj_obj_relative_pos_'):p.update(k=6,a='chair',ref='table');opts={'lr':['left','right'],'nf':['near','far'],'ud':['up','down']}[t[-2:]]
    elif t=='room_size_estimation':
        p.update(floor_polygon_reviewed=True,floor_corners=[dict(frame=2,object='floor',uv=uv) for uv in ([100,600],[200,600],[200,700],[100,700])])
    return p,[f'{chr(65+i)}. {x}' for i,x in enumerate(opts)]

for t in sorted(FAMILIES):
    for i in range(3):
        def point_program(t=t,i=i):
            plan,options=program_spec(t)
            q=dict(question_type=t,question='Use the chair, table, plant and floor to answer the requested '+t+' question.',options=options)
            reviewed=dict(reviewed=True,question_sha256=digest(q),bindings=plan)
            unit='count' if t in ('object_counting','absolute_count') else 'degree' if t in ('camera_rotation','absolute_direction_object') else 'm2' if t=='room_size_estimation' else 'm'
            config=dict(question_units={t:dict(unit=unit,decimals=0 if unit in ('count','degree') else 2)})
            row=dict(q,qid=f'point/{t}/{i}',answer='0')
            return Program(PointScene(i),TemplateFixture(plan),config).execute(row,reviewed)
        capture('point_program/'+t,f'pinhole/{i}','derivgen.program.Program.execute',point_program)

# Canon's camera path supplies an untouched production-generator control, including
# its public wrapper, specification pin, canonical events and answer computation.
for i in range(3):
    def canonical_camera(i=i):
        from derivgen.canon import generate
        from derivgen.calculator import SPEC_SHA256
        t='camera_displacement';plan=dict(i=2,j=12+i*2,M=32)
        q=dict(question_type=t,question=f'How far between frame 2 and frame {12+i*2} of 32?',options=[])
        reviewed=dict(reviewed=True,question_sha256=digest(q),bindings=plan)
        config=dict(spec=dict(sha256=SPEC_SHA256),infrastructure_only=True,question_units={t:dict(unit='m',decimals=2)})
        return generate(PointScene(i),TemplateFixture(plan),config,dict(q,qid=f'canon/{i}',answer='0.5',infrastructure_only=True),reviewed)
    capture('control/canon_generate',f'pinhole/{i}','derivgen.canon.generate',canonical_camera)
