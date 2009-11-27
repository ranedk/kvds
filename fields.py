import copy
import sys
import kvds.helper
from django.utils import simplejson
from kvds.common import dict_to_model, construct_key 
from kvds.models import Model, Field
from kvds.exceptions import FieldError

class ForeignKeyManager(object):
    def __init__(self, v):
        self.id = v['id']
        self.modelname = v['modelname']
        self.key_prefix = v['key_prefix']

class ForeignKey(Field):
    """ This field stored a model, value must be a model
    """
    meta_name = 'foreign_fields'
    field_key = 'F__'
    manager = ForeignKeyManager
    def __init__(self,to, initval=None):
        self.to = to
        super(ForeignKey, self).__init__(initval=initval)
        
    @classmethod
    def pre_save(cls, model_obj, **kw):
        """ Foreignkey will always be a model, to save it call the
        models save method
        """
        for f in model_obj.foreign_fields.values():
            f.val.save()
   
    def make_model(self, k, v, **kw):
        #fobj = dict_to_model(self.to, v)
        fobj = ForeignKeyManager(v)
        return fobj
        
    @classmethod
    def create(cls, model_obj, mfields, o, init_get, **kw):
        """ If model data is not present, the value is set to
        ForeignKeyManager
        """
        if not hasattr(model_obj, cls.meta_name):
            return
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
        assert isinstance(val,self.to) or isinstance(val, ForeignKeyManager)
        getattr(obj,self.meta_name)[self.name].val = val
    
    def __get__(self, obj, objtype):
        #print "ForeignKey getting obj:", obj, "objtype:", objtype
        fo = getattr(obj, self.meta_name) 
        if isinstance(fo[self.name].val, ForeignKeyManager):
            fobj = fo[self.name].val
            klass = self.to
            kvds_obj = klass.get(id=fobj.id)
            fo[self.name].val = kvds_obj
        return fo[self.name].val

class ManyToManyFieldManager(object):
    def __init__(self, obj):
        self.obj_fields = obj

class ManyToManyField(Field):
    meta_name = 'many_to_many_fields'
    field_key = 'M__'
    manager = ManyToManyFieldManager
    def __init__(self,to, initval=None):
        self.to = to
        super(ManyToManyField, self).__init__(initval=initval)

    @classmethod
    def pre_save(cls, model_obj, **kw):
        for mtmf in model_obj.many_to_many_fields.values():
            for f in mtmf.val:
                f.save()

    def make_model(self, k, v, **kw):
        # TODO: this will also use init_get to return a manager and then the manager will handle the stuff 
        obj_models = []
        for val in v:
            fobj = dict_to_model(self.to, val)
            obj_models.append(fobj)
        return obj_models

    @classmethod
    def create(cls, model_obj, mfields, o, init_get, **kw):
        print "==================", init_get, model_obj, mfields, o
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
            assert isinstance(v,self.to) or isinstance(v, ManyToManyFieldManager)
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

