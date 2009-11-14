import copy
import sys
import helper
from django.utils import simplejson

class Field(object):
    def __init__(self, initval=None, index=False, primary_index=False):
        self.meta_name = 'fields'
        self.primary_index = primary_index
        self.index = index
        if self.primary_index:
            self.index = True
        self.name = ''
        self.val = initval
        self.key = self.name
    
    def __get__(self, obj, objtype):
        #print "Field getting obj:", obj, "objtype:", objtype
        return obj.fields[self.name].val

    def __set__(self, obj, val):
        #print "Field setting ", obj, val
        obj.fields[self.name].val = val

    def __deepcopy__(self, memodict):
        obj = copy.copy(self)
        return obj

class ForeignKey(Field):
    def __init__(self, initval=None):
        super(ForeignKey, self).__init__(initval=initval)
        self.meta_name = 'foreign_fields'
        self.key = 'F__' + self.name

    def __set__(self, obj, val):
        assert isinstance(val,Model) or isinstance(val, ForeignKeyManager)
        obj.foreign_fields[self.name].val = val
    
    def __get__(self, obj, objtype):
        #print "ForeignKey getting obj:", obj, "objtype:", objtype
        if isinstance(obj.foreign_fields[self.name].val, ForeignKeyManager):
            fobj = obj.foreign_fields[self.name].val
            klass = globals()[fobj.modelname]
            kvds_obj = klass.get(id=fobj.id)
            obj.foreign_fields[self.name].val = kvds_obj
        return obj.foreign_fields[self.name].val

class ManyToManyField(Field):
    def __init__(self, initval=None):
        super(ManyToManyField, self).__init__(initval=initval)
        self.meta_name = 'many_to_many_fields'
        self.key = 'M__' + self.name

class ForeignKeyManager(object):
    def __init__(self, id, modelname, key_prefix):
        self.id = id
        self.modelname = modelname
        self.key_prefix = key_prefix
    
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

        new_class.add_to_class('_meta',{})
        for obj_name, obj in attrs.items():
            if isinstance(obj, Field):
                obj.name = obj_name
                if not new_class._meta.get(obj.meta_name):
                    new_class._meta[obj.meta_name] = {}
                new_class._meta[obj.meta_name].update({obj.name:obj})
                print obj.meta_name, obj.name, obj
                new_class.add_to_class(obj_name, obj)
            else:
                new_class.add_to_class(obj_name, obj)
            
        return new_class
    
    def add_to_class(cls, name, value):
            setattr(cls, name, value)
    
class Model(object):
    __metaclass__ = ModelBase
    
    def __init__(self, init_meta=False, **o):
        self.is_saved = False

        for meta_field in self._meta.keys():
            if not hasattr(self, meta_field):
                setattr(self, meta_field,{})
            for k,v in self._meta[meta_field].items():
                getattr(self, meta_field).update({ k : copy.deepcopy(v)})
        
        if not o.get('id'):
            o['id'] = helper.uuid()
        d = self.fields.keys()
        d.remove('modelname')
        d.remove('key_prefix')
        for prop in d: self.fields[prop].val = o.get(prop)
        if init_meta:
            for prop in self.foreign_fields.keys():
                f_m = o.get(prop)
                if f_m:
                    self.foreign_fields[prop].val = ForeignKeyManager(f_m.id, f_m.modelname, f_m.key_prefix)
                else:
                    self.foreign_fields[prop].val = None
        else:
            if hasattr(self,'foreign_fields'):
                for prop in self.foreign_fields.keys(): self.foreign_fields[prop].val = o.get(prop)

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
        data.update(dict((f.name, f.val) for f in self.fields.values()))
        for f in self.foreign_fields.values():
            if not f.val: continue
            f_key = "F__%s" % f.name
            data[f_key] = {} 
            data[f_key].update({'id':f.val.id}) 
            data[f_key].update({'modelname':f.val.modelname}) 
            data[f_key].update({'key_prefix':f.val.key_prefix}) 
        return data

    def savem2m(self):
        for f in self.foreign_fields.values():
            f.val.savem2m()
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
        if k.startswith('F__'):
            k = k.replace('F__','',1)
            fobj = dict_to_model(v)
            o.update({str(k):fobj})
        else:
            o.update({str(k):v})
    obj = klass(init_meta=fmodel, **o)
    return obj

class Bmodel(Model):
    key_prefix = 'kvds__b__comment'
    b1 = Field()
    b2 = Field()

class Amodel(Model):
    key_prefix = 'kvds__a__comment'
    a1 = Field()
    a2 = Field()
    a3 = ForeignKey()

class Comment(Model):
    key_prefix = 'kvds__comment'
    tmp = Field()
    tmp1 = Field(index = True)
    tmpf = ForeignKey()

#sample run
bitem = Bmodel(b1='itemb1',b2='itemb2')
aitem = Amodel(a1='itema1', a2='itema2', a3=bitem)
c = Comment(tmp='Rane was here', tmp1=['sdfsd','56ffg',456], tmpf=aitem)

#c.savem2m()
