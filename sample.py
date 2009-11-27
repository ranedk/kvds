from kvds.models import *
from kvds.fields import *

class Bmodel(Model):
    key_prefix = 'kvds__b__comment'
    b1 = Field()
    b2 = Field()

class Amodel(Model):
    key_prefix = 'kvds__a__comment'
    a1 = Field()
    a2 = Field()
    a3 = Field()

class Cmodel(Model):
    key_prefix = 'kvds__c__comment'
    c1 = Field()
    c2 = Field()
    c3 = Field()

class Comment(Model):
    key_prefix = 'kvds__comment'
    tmp = Field()
    #tmp1 = ManyToManyField(Amodel)
    tmpf = ForeignKey(Cmodel)
    ptmp = Field(index=True)

#sample run
bitem = Bmodel(b1='itemb1',b2='itemb2')
a1item = Amodel(a1='itema1a1', a2='itema1a2', a3='itema1a3')
a2item = Amodel(a1='itema2a1', a2='itema2a2', a3='itema2a3')
citem = Cmodel(c1='itemc1', c2='itemc2', c3='itemc3')
c = Comment(tmp='Rane was here', tmp1=[a1item,a2item], tmpf=citem, ptmp='rane')
#c = Comment(tmp='Rane was here', tmpf=citem, ptmp='rane')

#c.save()
