import maya.cmds as mc
###------------------------------FUNCTION------------------------------
def createCtlGrp(names,targs,shape='circle',size=1):
    for name, targ in zip(names,targs):
        ctl = customNURBScircle(shape, size=size, name=name)
        nul = mc.group(ctl, n=ctl+'_nul')

        const1 = mc.parentConstraint(targ, nul, mo=False)
        mc.delete(const1)

def customNURBScircle(shape, size, name=''):
    if shape =='circle':
        ctl = mc.circle(nr=(1,0,0),n=name, r=size, d=1)[0] #degree=1(linear)

    elif shape =='square':
        ctl = mc.circle(nr=(1,0,0),n=name, r=size, sections=4, d=1)[0]

    mc.delete(ctl, constructionHistory=True)
    return ctl
    
def overrideColor(crvs, color='yellow'):
    if isinstance(crvs,str): crvs = [crvs]
    
    if color=='yellow': idx = 17
    elif color=='magenta': idx = 9
    else: idx = 0
    
    for crv in crvs:
        try:
            mc.setAttr(crv+'.overrideEnabled', 1)
            mc.setAttr(crv+'.overrideColor', idx)
        except:
            print('ERROR: overrideColor failed:', crv) ##use raise instead
                    
def parentConstIterate(parents, childs):
    for parent, child in zip(parents, childs):
        const1 = mc.parentConstraint(parent, child, mo=True)[0]
        mc.setAttr(const1+'.interpType', 2) #shortest
        
def parentIterate(parents, childs):
    for parent, child in zip(parents, childs):
        mc.parent(child, parent)
        

###------------------------------CLASS---------------------------------
class stretchyIKMaker():
    def __init__(self, chain, section=1, degree=3, prefix=''):
        self.chain = chain
        self.start = chain[0]
        self.end = chain[-1]
        self.span = section + 1
        self.degree = degree
        
        self.crv = prefix + 'spineIk_Crv'
        self.ikHand = prefix + 'spineIk'
        self.ikEff = prefix + 'effector'
        
        nameRef = ['start']+['%02d'%d for d in range(section)]+['end']
        nameRef = [prefix + d for d in nameRef]
        
        self.clsGrp = prefix + 'cls_Grp'
        self.clsNodes = [d+'_cls' for d in nameRef]
        self.clsHandles = [d+'_clsHandle' for d in nameRef]
        
        self.ctlGrp = prefix + 'ctl_Grp'
        self.FKCtls = [d+'_FK_ctl' for d in nameRef]
        self.IKCtls = [d+'_IK_ctl' for d in nameRef]
        

        self.createCrv()
        self.rebuildCrv()
        self.createIKHandle()
        self.clsOnCrv()
        self.ctlOnCls()
        self.connectCtl()
        self.ikTwist()
    
    def createCrv(self):
        posList = []
        for i in self.chain:
            pos= mc.xform(i, q=True, ws=True, t=True)
            posList.append(pos)
            
        mc.curve(p=posList, n=self.crv, d=self.degree)
    
    def rebuildCrv(self):
        mc.rebuildCurve(self.crv, ch=0, rpo=1, rt=0, end=1,
                        kr=2, kcp=0, kep=0, kt=0,
                        s=self.span, d=3, tol=0.01
                        )
                        
    def createIKHandle(self):
        ikNode = mc.ikHandle(sj=self.start, ee=self.end, c=self.crv, ccv=False,
                    sol='ikSplineSolver', s='sticky', 
                    )
        mc.rename(ikNode[0],self.ikHand)
        mc.rename(ikNode[1],self.ikEff)
        
    def clsOnCrv(self):
        CVs = mc.ls(self.crv + '.cv[*]', fl=1)

        targs = (
            [CVs[0:2]]
            +[c for c in CVs[2:-2]]
            +[[CVs[-2],CVs[-1]]]
        )

        for targ, clus in zip(targs, self.clsNodes):
            mc.cluster(targ, n=clus, rel=True)
        
        mc.group(self.clsHandles,n=self.clsGrp)
    
    def ctlOnCls(self):
        
        createCtlGrp(self.clsHandles, self.IKCtls, None, shape='square', size=1)
        createCtlGrp(self.clsHandles, self.FKCtls, None, shape='circle', size=.7)
        offsetCtls(self.IKCtls+self.FKCtls, r=(0,90,0), s=(1.5,1.5,2))
  
        overrideColor(self.IKCtls, color='yellow')
        overrideColor(self.FKCtls, color='magenta')
        
        FKNul=[d+'_nul' for d in self.FKCtls]
        parentIterate(self.IKCtls, FKNul)
        
        IKNul=[d+'_nul' for d in self.IKCtls]
        FKNul=[d+'_nul' for d in self.FKCtls]
        IKNul=[d+'_nul' for d in self.IKCtls]
        
        parentIterate(self.FKCtls, IKNul)

        for i,nul in enumerate(FKNul):
            ori = mc.orientConstraint(self.start,self.end,nul,mo=False)[0]
            val = i /(len(FKNul)-1)
            mc.setAttr( '%s.%sW0'%(ori,self.start), 1-val )
            mc.setAttr( '%s.%sW1'%(ori,self.end), val )
            mc.delete(ori)

        
        for i in range(len(FKNul)-1):
            mc.parent(FKNul[i+1], self.FKCtls[i])

        
    def connectCtl(self):
        parentConstIterate(self.FKCtls, self.clsHandles)

    def ikTwist(self):
        mc.spaceLocator(n=self.upObj)
        mc.parent(self.upObj,self.FKCtls[0]+'_orient', r=True)
        mc.move(0,100,0,'tongue_upObj', ls=True)
        mc.hide(self.upObj)
        
        mc.setAttr(self.ikHand+'.dTwistControlEnable', 1)
        mc.setAttr(self.ikHand+'.dWorldUpType', 1)
        mc.connectAttr(self.upObj+'.worldMatrix', self.ikHand+'.dWorldUpMatrix')

###------------------------------EXECUTE---------------------------------
if __name__ == "__main__":
    sel=mc.ls(sl=True)
    run01=stretchyIKMaker(sel,section=2,prefix='test_',degree=3)

