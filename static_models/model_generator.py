import os
import re
import pathlib
from django.conf import settings
from django.http.request import HttpRequest
from django.core.files.base import ContentFile
#from django.core.files.storage import FileSystemStorage
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
        A model (not instance) or list of dictionaries. 
    view
        Must be at least a DetailView
    storage
        Pass a storage class or insttance. If a class, a path will be 
        built, if not the class is used as given. Amongst other 
        possibilities, allows storage to cloud services. Default is
        FileSystemStorage.
    overwrite
        attempt file deletion before creation (no error thrown). Note
        that if not overwriting, storage systems such as the default may 
        attempt renaming rather than file overwriting.
    path_includes_view
        Path includes the view name. Default False
    id_fieldname
        By default, the class writes and locates files using the pk as
        id. But if this parameter is set, it uses the value from this
        fieldname instead. Most likely use is on a slugfield.
    extension
        can be None. Dot is added automatically.
    '''
    def __init__(self, 
        data,
        view,
        subpath='',
        overwrite=True,
        path_includes_view=False,
        id_fieldname='pk',
        extension=None,
    ):
        self.is_model = issubclass(data, models.Model)
        self.data = data
        if isinstance(view, type):
            view = view()
        self.view = view
        self.view.request = HttpRequest()       
        self.overwrite = overwrite

        # decide a path from the configured dir to this view output
        if (not subpath and self.is_model):
            subpath = self.data._meta.model_name
            if (path_includes_view):
                subpath = os.path.join(subpath,
                self.camelcase_to_underscore(self.view.__class__.__name__)
            )
        self.static_pathroot = os.path.join(settings.staticmodels_dir, subpath)
        
        # make the dirs
        os.makedirs(self.static_pathroot, exist_ok=True)
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

        dst = self.get_full_path(obj)
        isfile = os.path.isfile(dst) 
        if((not isfile) or self.overwrite):
            with open(dst, 'wb') as fd:  
                fd.writelines(cf.open())  
        return dst
                
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
        for obj in objs:
            self._create(obj)
        return len(objs)

    def _delete(self, obj):
        try:
            os.remove(self.get_full_path(obj))
        except FileNotFoundError:
            pass
            
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
        for obj in objs:
            self._delete(obj)
        return len(objs)
        

# class ModelGenerator():
    # '''
    # Generate static files from a Model.
    
    # model
        # A model to use for finding page data
    # view
        # Must be at least a DetailView
    # storage
        # Pass a storage class or insttance. If a class, a path will be 
        # built, if not the class is used as given. Amongst other 
        # possibilities, allows storage to cloud services. Default is
        # FileSystemStorage.
    # overwrite
        # attempt file deletion before creation (no error thrown). Note
        # that if not overwriting, storage systems such as the default may 
        # attempt renaming rather than file overwriting.
    # path_includes_view
        # Path includes the view name. Default False
    # id_fieldname
        # By default, the class writes and locates files using the pk as
        # id. But if this parameter is set, it uses the value from this
        # fieldname instead. Most likely use is on a slugfield.
    # extension
        # can be None. Dot is added automatically.
    # '''
    # def __init__(self, 
        # model,
        # view,
        # storage=FileSystemStorage,
        # overwrite=True,
        # path_includes_view=False,
        # id_fieldname=None,
        # extension=None,
    # ):
        # self.model = model
        # if isinstance(view, type):
            # view = view()
        # self.view = view
        # self.view.request = HttpRequest()
        # self.storage = storage
        # if isinstance(storage, type):
            # self.storage = storage()         
        # self.overwrite = overwrite
        # self.app_subpath = os.path.join('site', self.model._meta.model_name)
        # if (path_includes_view):
            # self.app_subpath  = os.path.join(self.app_subpath,
                # self.camelcase_to_underscore(self.view.__class__.__name__)
            # )
        # self.id_fieldname = id_fieldname
        # if (extension is None):
            # extension = ''
        # if (extension):
            # extension = '.' + extension        
        # self.extension = extension
        
    # @property
    # def location(self):
        # '''
        # Return a human readable location for the files.
        # For display, not good for code.
        # return
            # If the files are local, the base filepath, else the app_subpath.
        # '''
        # #? Don't know enough to risk returning storage.url, which can 
        # # be not implemented.
        # if hasattr(self.storage, 'location'):
            # # its a localfile
            # path = os.path.join(self.storage.location, self.app_subpath)
        # else:
            # path = self.app_subpath
        # return path
                
    # def camelcase_to_underscore(self, s):
        # # A utility for generating a filename from view classes
        # # Lifted from someplace in Django?
        # # https://djangosnippets.org/snippets/585/
        # return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s).lower().strip('_')

    # def get_id(self, obj):
        # _id=None
        # # start with pk
        # if (not self.id_fieldname):
            # _id = obj.pk
        # else:
            # _id = getattr(obj, self.id_fieldname)
        # return _id

    # def get_full_path(self, obj):
        # filename = str(self.get_id(obj)) + self.extension
        # return os.path.join(self.app_subpath, filename)
                
    # def _create(self, obj):
        # self.view.object = obj
        # ctx = self.view.get_context_data()
        # tr = self.view.render_to_response(ctx)
        
        # # Above only caches data, resolve
        # tr = tr.render()
        
        # # Gets the data itself
        # #! still bytes
        # #! where stripped?
        # f = ContentFile(tr.content, name=None)

        # dst = self.get_full_path(obj)
        # if (self.overwrite):
            # self.storage.delete(dst)
        # # name, content max_length
        # return self.storage.save(
            # dst, 
            # f, 
            # max_length=None
        # )
                
    # def create(self, _id):
        # field = self.id_fieldname if(self.id_fieldname) else 'pk'
        # obj = self.model.objects.get({field : self.get_id(obj)})
        # self._create(obj)
        
    # def obj_create(self, obj):
        # self._create(obj)
        
    # def all_create(self):
        # objs = self.model.objects.all()
        # for obj in objs:
            # self._create(obj)
        # return len(objs)

    # def _delete(self, obj):
        # self.storage.delete(self.get_full_path(obj))

    # def delete(self, _id):
        # field = self.id_fieldname if(self.id_fieldname) else 'pk'
        # obj = self.model.objects.get({field : self.get_id(obj)})
        # self._delete(obj)
        
    # def obj_delete(self, obj):
        # self._delete(obj)
        
    # def all_delete(self):
        # objs = self.model.objects.all()
        # for obj in objs:
            # self._delete(obj)
        # return len(objs)
        
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
