from models import *
from fields import *

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
    tmp1 = ManyToManyField()
    tmpf = ForeignKey()
    ptmp = Field(index=True)

#sample run
bitem = Bmodel(b1='itemb1',b2='itemb2')
aitem = Amodel(a1='itema1', a2='itema2', a3='itema3')
citem = Cmodel(c1='itemc1', c2='itemc2', c3='itemc3')
c = Comment(tmp='Rane was here', tmp1=[aitem,bitem], tmpf=citem, ptmp='rane')

c.savem2m()
