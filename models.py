import copy
import sys
import helper
from django.utils import simplejson

class Field(object):
    #TODO: add required field
    #TODO: add add() for many to many field
    meta_name = 'fields'
    field_key = ''
    def __init__(self, initval=None, index=False, required=True, primary_index=False):
        self.required = required
        self.primary_index = primary_index
        self.index = index
        if self.primary_index:
            self.index = True
        self.name = ''
        self.val = initval
    
    @classmethod
    def pre_save(cls, model_obj, **kw):
        pass
    
    @classmethod
    def make_model(cls, k, v, **kw):
        return v

    @classmethod
    def create(cls, model_obj, mfields, o, init_get=False, **kw):
        if not hasattr(model_obj,cls.meta_name):
            return
        d = mfields.keys()
        d.remove('modelname')
        d.remove('key_prefix')
        for prop in d: setattr(model_obj, prop, o.get(prop))
        
    @classmethod
    def data(cls, model_obj, **kw):
        return dict((f.name, f.val) for f in model_obj.fields.values())
    
    def __get__(self, obj, objtype):
        #print "Field getting obj:", obj, "objtype:", objtype
        fo = getattr(obj, self.meta_name) 
        return fo[self.name].val

    def __set__(self, obj, val):
        if self.required:
            if not val:
                raise FieldError("%s is a required Field" % (self.name))
        #print "Field setting ", obj, val
        fo = getattr(obj, self.meta_name) 
        fo[self.name].val = val

    def __deepcopy__(self, memodict):
        obj = copy.copy(self)
        return obj

class ForeignKey(Field):
    meta_name = 'foreign_fields'
    field_key = 'F__'
    def __init__(self, initval=None):
        super(ForeignKey, self).__init__(initval=initval)
        
    @classmethod
    def pre_save(cls, model_obj, **kw):
        for f in model_obj.foreign_fields.values():
            f.val.savem2m()
    
    @classmethod
    def make_model(cls, k, v, **kw):
        fobj = dict_to_model(v)
        return fobj
        
    @classmethod
    def create(cls, model_obj, mfields, o, init_get, **kw):
        if not hasattr(model_obj,cls.meta_name):
            return
        if init_get:
            for prop in model_obj.foreign_fields.keys():
                f_m = o.get(prop)
                if f_m:
                    model_obj.foreign_fields[prop].val = ForeignKeyManager(f_m.id, f_m.modelname, f_m.key_prefix)
                else:
                    model_obj.foreign_fields[prop].val = None
        else:
            for prop in model_obj.foreign_fields.keys(): 
                setattr(model_obj, prop, o.get(prop))
    
    @classmethod
    def data(cls, model_obj, **kw):
        data = {}
        for f in model_obj.foreign_fields.values():
            if not f.val: continue
            f_key = "%s%s" % (cls.field_key, f.name)
            data[f_key] = {} 
            data[f_key].update({'id':f.val.id}) 
            data[f_key].update({'modelname':f.val.modelname}) 
            data[f_key].update({'key_prefix':f.val.key_prefix}) 
        return data

    def __set__(self, obj, val):
        #print "ForeignKey Setter", obj, val
        if self.required:
            if not val:
                raise FieldError("%s is a required Field" % (self.name))
        assert isinstance(val,Model) or isinstance(val, ForeignKeyManager)
        getattr(obj,self.meta_name)[self.name].val = val
    
    def __get__(self, obj, objtype):
        #print "ForeignKey getting obj:", obj, "objtype:", objtype
        fo = getattr(obj, self.meta_name) 
        if isinstance(fo[self.name].val, ForeignKeyManager):
            fobj = fo[self.name].val
            klass = globals()[fobj.modelname]
            kvds_obj = klass.get(id=fobj.id)
            fo[self.name].val = kvds_obj
        return fo[self.name].val

class ForeignKeyManager(object):
    def __init__(self, id, modelname, key_prefix):
        self.id = id
        self.modelname = modelname
        self.key_prefix = key_prefix

class ManyToManyField(Field):
    meta_name = 'many_to_many_fields'
    field_key = 'M__'
    def __init__(self, initval=None):
        super(ManyToManyField, self).__init__(initval=initval)

    @classmethod
    def pre_save(cls, model_obj, **kw):
        for mtmf in model_obj.many_to_many_fields.values():
            for f in mtmf.val:
                f.savem2m()

    @classmethod
    def make_model(cls, k, v, **kw):
        obj_models = []
        for val in v:
            fobj = dict_to_model(val)
            obj_models.append(fobj)
        return obj_models

    @classmethod
    def create(cls, model_obj, mfields, o, init_get, **kw):
        if init_get:
            for prop in model_obj.many_to_many_fields.keys():
                mtmf = o.get(prop)
                if mtmf:
                    manager_obj = ManyToManyFieldManager(mtmf)
                    model_obj.many_to_many_fields[prop].val = manager_obj
        else:
            for prop in model_obj.many_to_many_fields.keys():
                setattr(model_obj, prop, o.get(prop))

    @classmethod
    def data(cls, model_obj, **kw):
        data = {}
        for mtmf in model_obj.many_to_many_fields.values():
            #import pdb; pdb.set_trace()
            if not mtmf.val: continue
            d = []
            for f in mtmf.val: 
                d.append({
                        'id' : f.id ,
                        'modelname' : f.modelname ,
                        'key_prefix' : f.key_prefix , 
                })
            f_key = "%s%s" % (mtmf.field_key, mtmf.name)
            data.update({f_key : d})
        return data

    def __set__(self, obj, val):
        #print "ManyToManyField Setter", val
        if self.required:
            if not val:
                raise FieldError("%s is a required Field" % (self.name))
        assert isinstance(val,type([]))
        for v in val:
            assert isinstance(v,Model) or isinstance(v, ManyToManyFieldManager)
        getattr(obj,self.meta_name)[self.name].val = val
    
    def __get__(self, obj, objtype):
        #print "ForeignKey getting obj:", obj, "objtype:", objtype
        d = []
        fo = getattr(obj, self.meta_name) 
        if isinstance(fo[self.name].val, ManyToManyFieldManager):
            for fobj in fo[self.name].val.obj_fields:
                klass = globals()[fobj.modelname]
                kvds_obj = klass.get(id=fobj.id)
                d.append(kvds_obj)          
            fo[self.name].val = d
        return fo[self.name].val

class ManyToManyFieldManager(object):
    def __init__(self, obj):
        self.obj_fields = obj

class ModelBase(type):
    """
    Metaclass for kvds models
    """
    def __new__(cls, name,bases,attrs):
        super_new = super(ModelBase, cls).__new__
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
 
        attrs['id'] = Field(primary_index=True)
        attrs['modelname'] = Field(initval=name)
        attrs['key_prefix'] = Field(initval=attrs.get('key_prefix',name))

        new_class.add_to_class('_meta', {})
        new_class.add_to_class('field_prefix', {})
        for obj_name, obj in attrs.items():
            if isinstance(obj, Field):
                obj.name = obj_name
                if not new_class._meta.get(obj.meta_name):
                    new_class._meta[obj.meta_name] = {}
                new_class._meta[obj.meta_name].update({obj.name:obj})
                #print obj.meta_name, obj.name, obj.field_key , obj
                new_class.field_prefix.update({obj.field_key:obj.__class__})
                new_class.add_to_class(obj_name, obj)
            else:
                new_class.add_to_class(obj_name, obj)
            
        return new_class
    
    def add_to_class(cls, name, value):
            setattr(cls, name, value)
    
class Model(object):
    __metaclass__ = ModelBase
    
    def __init__(self, init_get=False, **o):
        self.is_saved = False

        for meta_field in self._meta.keys():
            if not hasattr(self, meta_field):
                setattr(self, meta_field,{})
            for k,v in self._meta[meta_field].items():
                getattr(self, meta_field).update({ k : copy.deepcopy(v)})
        
        if not o.get('id'):
            o['id'] = helper.uuid()
        
        for fattrs in self._meta.keys():
            mfields = getattr(self,fattrs)
            klass = mfields.values()[0].__class__
            klass.create(self, mfields, o, init_get)

    @classmethod
    def filter(cls, **kw):
        pass
        #implement filter methos of indexed keys
        # -- indexedkeys give value of main primary key, which in turn has the data
        # -- for indexed keys, implement get at kvds layer which get data for key inside the give key, this acts as one to one mapping
        # -- at kvds implement get_related call, which will get data for all keys inside a list of keys for the given key
        # this will work a a many to many field
        # use the above many to many to also implement a foreign field data which get complete model for a given key including foreign keys
        # method should also have a call where user can ask only for particular set of keys

    @classmethod
    def get(cls, **kw):
        o = cls.get_dict(**kw)
        m = dict_to_model(o)
        m.is_saved = True
        return m
    
    @classmethod
    def get_dict(cls, **kw):
        assert len(kw) == 1
        k, v = kw.items()[0]
        field = cls._meta['fields'].get(k)
        assert field
        assert field.index
        key = construct_key(cls._meta['fields']['key_prefix'].val, k, v)
        o = simplejson.loads(helper.kvds(key=key)[key])
        return o

    def __related_data__(self):
        data = {}
        data.update(dict((f.name, f.val) for f in self.fields.values()))
        for f in self.foreign_fields.values():
            f_key = "F__%s" % f.name
            data[f_key] = {}
            data[f_key].update(f.val.__related_data__()) 
        return data
    
    def __data__(self):
        data = {}
        for fattrs in self._meta.keys():
            mfields = getattr(self,fattrs)
            klass = mfields.values()[0].__class__
            data.update(klass.data(self))
        return data

    def savem2m(self):
        for fattrs in self._meta.keys():
            mfields = getattr(self,fattrs)
            klass = mfields.values()[0].__class__
            klass.pre_save(self)
        data = self.__data__()
        key = construct_key(self.key_prefix, "id", self.id)
        #print key, "=>", simplejson.dumps(data)
        helper.kvds(key=key, value=simplejson.dumps(data))
        self.is_saved = True

def construct_key(key_prefix, keyname, key):
    return ("%s.%s__%s" % (key_prefix, keyname, key)).lower()

def dict_to_model(d, fmodel=True):
    klass = globals()[d['modelname']]
    o = {}
    for k,v in d.items():
        for fk, field_klass in klass.field_prefix.items():
            if k.startswith(fk):
                k = k.replace(fk ,'',1)
                fobj = field_klass.make_model(k,v)
                o.update({str(k):fobj})
    obj = klass(init_get=fmodel, **o)
    return obj

class FieldError(Exception):
    "The requested view does not exist"
    pass

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

#sample run
bitem = Bmodel(b1='itemb1',b2='itemb2')
aitem = Amodel(a1='itema1', a2='itema2', a3='itema3')
citem = Cmodel(c1='itemc1', c2='itemc2', c3='itemc3')
c = Comment(tmp='Rane was here', tmp1=[aitem,bitem])

#c.savem2m()
