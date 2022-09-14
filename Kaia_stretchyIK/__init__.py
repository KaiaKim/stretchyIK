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
    def __init__(self, chain, section=1, degree=3, prefix='', softCorner=True):
        self.chain = chain
        self.start = chain[0]
        self.end = chain[-1]
        self.span = section + 1
        self.degree = degree
        self.softCorner = softCorner
        
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
        
        '''
        self.createCrv()
        self.rebuildCrv()
        self.createIKHandle()
        self.clsOnCrv()
        self.ctlOnCls()
        self.connectCtl()
        '''
    
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
        
    def clsOnCrv(self, softCorner=True):
        CVs = mc.ls(self.crv + '.cv[*]', fl=1)
        
        if self.softCorner == True:
            clsTarget = [CVs[0:2]] + [c for c in CVs[2:-2]] + [CVs[-2],CVs[-1]]
        elif self.softCorner == False:
            clsTarget = [CVs[0], CVs[1:-1], CVs[-1]]

        for cv, clus in zip(clsTarget, self.clsNodes):
            mc.cluster(cv, n=clus, rel=True)

        
        mc.group(self.clsHandles,n=self.clsGrp)
    
    def ctlOnCls(self):
        
        createCtlGrp(self.IKCtls, self.clsHandles, shape='square', size=8)
        createCtlGrp(self.FKCtls, self.clsHandles, shape='circle', size=4)
        
        overrideColor(self.IKCtls, color='yellow')
        overrideColor(self.FKCtls, color='magenta')
        
        FKNul=[d+'_nul' for d in self.FKCtls]
        parentIterate(self.IKCtls, FKNul)
        
        IKNul=[d+'_nul' for d in self.IKCtls]
        '''        
        startOri = mc.getAttr(self.start+'.jointOrient')[0] #joint orient
        endOri = mc.getAttr(self.end+'.jointOrient')[0]
        midOri = (
                    startOri[0]+endOri[0] /2,
                    startOri[1]+endOri[1] /2,
                    startOri[2]+endOri[2] /2
                    )
        
        
        for i in range(len(IKNul)-2):
            mc.rotate(midOri[0],midOri[1],midOri[2],IKNul[i+1])
        mc.rotate(endOri[0],endOri[1],endOri[2],IKNul[-1])
        '''

        for i,nul in enumerate(IKNul):
            print(nul)
            ori = mc.orientConstraint(self.start,self.end,nul,mo=False)[0]
            val = i /(len(IKNul)-1)
            mc.setAttr( '%s.%sW0'%(ori,self.start), 1-val )
            mc.setAttr( '%s.%sW1'%(ori,self.end), val )
            mc.delete(ori)

        
        for i in range(len(IKNul)-1):
            mc.parent(IKNul[i+1], self.IKCtls[i])

        
    def connectCtl(self):
        parentConstIterate(self.FKCtls, self.clsHandles)


###------------------------------EXECUTE---------------------------------
sel=mc.ls(sl=True)
run01=stretchyIKMaker(sel,section=2,prefix='tongue_',degree=3,softCorner=True)

run01.createCrv()
run01.rebuildCrv()
run01.createIKHandle()
run01.clsOnCrv()
run01.ctlOnCls()
run01.connectCtl()
