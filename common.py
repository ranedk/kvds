def dict_to_model(klass, d, fmodel=True):
    o = {}
    for k,v in d.items():
        fkey = k.split('__')[0]
        field_obj = klass.field_prefix.get('%s__' % fkey)
        if not field_obj:
            field_obj = klass.field_prefix['']
            fname = fkey
        else:
            fname = k.split('__')[1]
        fobj = field_obj.make_model(fname,v)
        o.update({str(fname):fobj})
    obj = klass(init_get=fmodel, **o)
    return obj

def construct_key(key_prefix, keyname, key):
    return ("%s.%s__%s" % (key_prefix, keyname, key)).lower()
