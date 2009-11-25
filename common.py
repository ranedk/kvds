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

def construct_key(key_prefix, keyname, key):
    return ("%s.%s__%s" % (key_prefix, keyname, key)).lower()
