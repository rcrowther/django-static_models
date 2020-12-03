import os
import re
import pathlib
from django.conf import settings
from django.http.request import HttpRequest
from django.core.files.base import ContentFile
from static_models.settings import settings
from django.db import models




#[{'slug': 'about'},{'slug': 'terms'}, {'slug': 'contact'}], 'mud.views.site_pages_view.SitePagesView'),

class ModelManager():
    '''
    Generate static files from a Model.
    
    If the data is a model it should not be an instance. The code will 
    assume the view is generic and set the model.
    If the data is a list of dicts the code will pass each dict to the 
    view context.  
    In both cases, the id of the object, and so the filename, will be 
    taken from id_fieldname.
    data
        A model (not instance), or list of dictionaries. 
    view
        Must be at least a DetailView
    pathroot
        Path from the configured rootdir to the output of this class.
        If empty, the pathroot is empty, unless the data is a model,
        in which case it defaults to a modelname and opetional 
        viewname. .
    overwrite
        overwrite existing generated files. Default is False.
    path_includes_view
        Path includes the view name. Default False
    id_fieldname
        The value from this fieldname is used to provide the filename.
        Most likely targets a slugfield. Default is 'pk'
    extension
        Optional extension name. Dot is added automatically.
    '''
    def __init__(self, 
        data,
        view,
        pathroot='',
        overwrite=False,
        path_includes_view=False,
        id_fieldname=None,
        extension=None,
    ):
        self.is_model = not( isinstance(data, list))
        self.data = data
        if isinstance(view, type):
            view = view()
        self.view = view
        self.view.request = HttpRequest()       
        self.overwrite = overwrite

        # decide a path from the configured dir to this view output
        if (not pathroot and self.is_model):
            pathroot = self.data._meta.model_name
            if (path_includes_view):
                pathroot = os.path.join(pathroot,
                self.camelcase_to_underscore(self.view.__class__.__name__)
            )
        self.static_pathroot = os.path.join(settings.staticmodels_dir, pathroot)
        
        # make the dirs
        os.makedirs(self.static_pathroot, exist_ok=True)
        if (not id_fieldname):
            id_fieldname = 'pk'
        self.id_fieldname = id_fieldname
        extension = ''
        if (extension):
            extension = '.' + extension        
        self.extension = extension
        
    @property
    def location(self):
        '''
        Return a human readable location for the files.
        For display, not good for code.
        return
            If the files are local, the base filepath, else the static_pathroot.
        '''
        return self.static_pathroot
                
    def camelcase_to_underscore(self, s):
        # A utility for generating a filename from view classes
        # Lifted from someplace in Django?
        # https://djangosnippets.org/snippets/585/
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s).lower().strip('_')

    def get_id(self, obj):
        _id=None
        
        # defaults to pk
        if (self.is_model):
            _id = getattr(obj, self.id_fieldname) 
        else:
            _id = obj[self.id_fieldname]             
        return _id

    def get_full_path(self, obj):
        filename = str(self.get_id(obj)) + self.extension
        return os.path.join(self.static_pathroot, filename)
                
    def _create(self, obj):
        dst = self.get_full_path(obj)
        isfile = os.path.isfile(dst) 
        if((not isfile) or self.overwrite):
            if (self.is_model):
                self.view.object = obj
                ctx = self.view.get_context_data()
            else:
                ctx = self.view.get_context_data(**obj)
            tr = self.view.render_to_response(ctx)
            
            # Above only caches data, resolve
            tr = tr.render()
            
            # Gets the data itself
            #! still bytes
            #! where stripped?
            cf = ContentFile(tr.content, name=None)
            with open(dst, 'wb') as fd:  
                fd.writelines(cf.open())  
            return dst
        return None
        
    def create(self, _id):
        obj = None
        if (self.is_model):
            obj = self.data.objects.get((self.id_fieldname, _id))
        else:
            for datum in self.data:
                if (datum[self.id_fieldname] == _id):
                    obj = datum        
        return self._create(obj)
        
    def obj_create(self, obj):
        self._create(obj)
        
    def all_create(self):
        if (self.is_model):
            objs = self.data.objects.all()
        else:
            objs = self.data
        count = 0
        for obj in objs:
            #print(obj)
            r = self._create(obj)
            if (r):
                count += 1 
        return count

    def _delete(self, obj):
        try:
            os.remove(self.get_full_path(obj))
        except FileNotFoundError:
            return None
        return 1
            
    def delete(self, _id):
        obj = None
        if (self.is_model):
            obj = self.data.objects.get((self.id_fieldname, _id))
        else:
            for datum in self.data:
                if (datum[self.id_fieldname] == _id):
                    obj = datum
        self._delete(obj)
        
    def obj_delete(self, obj):
        self._delete(obj)
        
    def all_delete(self):
        if (self.is_model):
            objs = self.data.objects.all()
        else:
            objs = self.data
        count = 0
        for obj in objs:
            r = self._delete(obj)
            if (r):
                count += 1
        return count
        

        
def file_static_merge(obj, view):
    '''
    Preconfigured Filesystem save.
    PK for id and overwriting.
    '''
    print("static_merge!")
    g = ModelManager(obj._meta.model, view, overwrite=True)
    g.obj_create(obj)

def file_static_delete(obj, view):
    '''
    Preconfigured Filesystem delete.
    PK for id.
    '''
    g = ModelManager(obj._meta.model, view)
    g.obj_delete(obj)
