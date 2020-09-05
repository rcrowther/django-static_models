import os
import re
from django.conf import settings

from django.http.request import HttpRequest

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage



#! probably require slug name parameter
class ModelGenerator():
    '''
    Generate static files from a Model.
    
    model
        A model to use for finding page data
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
        model,
        view,
        storage=FileSystemStorage,
        overwrite=True,
        path_includes_view=False,
        id_fieldname=None,
        extension=None,
    ):
        self.model = model
        if isinstance(view, type):
            view = view()
        self.view = view
        self.view.request = HttpRequest()
        self.storage = storage
        if isinstance(storage, type):
            self.storage = storage()         
        self.overwrite = overwrite
        self.app_subpath = os.path.join('site', self.model._meta.model_name)
        if (path_includes_view):
            self.app_subpath  = os.path.join(self.app_subpath,
                self.camelcase_to_underscore(self.view.__class__.__name__)
            )
        self.id_fieldname = id_fieldname
        if (extension is None):
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
            If the files are local, the base filepath, else the app_subpath.
        '''
        #? Don't know enough to risk returning storage.url, which can 
        # be not implemented.
        if hasattr(self.storage, 'location'):
            # its a localfile
            path = os.path.join(self.storage.location, self.app_subpath)
        else:
            path = self.app_subpath
        return path
                
    def camelcase_to_underscore(self, s):
        # Autility for generating a filename from view classes
        # Lifted from someplace in Django?
        # https://djangosnippets.org/snippets/585/
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s).lower().strip('_')

    def get_id(self, obj):
        _id=None
        # start with pk
        if (not self.id_fieldname):
            _id = obj.pk
        else:
            _id = getattr(obj, self.id_fieldname)
        return _id

    def get_full_path(self, obj):
        filename = str(self.get_id(obj)) + self.extension
        return os.path.join(self.app_subpath, filename)
                
    def _create(self, obj):
        self.view.object = obj
        ctx = self.view.get_context_data()
        tr = self.view.render_to_response(ctx)
        
        # Above only caches data, resolve
        tr = tr.render()
        
        # Gets the data itself
        #! still bytes
        #! where stripped?
        f = ContentFile(tr.content, name=None)

        dst = self.get_full_path(obj)
        if (self.overwrite):
            self.storage.delete(dst)
        # name, content max_length
        return self.storage.save(
            dst, 
            f, 
            max_length=None
        )
                
    def create(self, _id):
        field = self.id_fieldname if(self.id_fieldname) else 'pk'
        obj = self.model.objects.get({field : self.get_id(obj)})
        self._create(obj)
        
    def obj_create(self, obj):
        self._create(obj)
        
    def all_create(self):
        objs = self.model.objects.all()
        for obj in objs:
            self._create(obj)
        return len(objs)

    def _delete(self, obj):
        self.storage.delete(self.get_full_path(obj))

    def delete(self, _id):
        field = self.id_fieldname if(self.id_fieldname) else 'pk'
        obj = self.model.objects.get({field : self.get_id(obj)})
        self._delete(obj)
        
    def obj_delete(self, obj):
        self._delete(obj)
        
    def all_delete(self):
        objs = self.model.objects.all()
        for obj in objs:
            self._delete(obj)
        return len(objs)
        
def file_static_merge(obj, view):
    '''
    Preconfigured Filesystem save.
    PK for id and overwriting.
    '''
    print("static_merge!")
    g = ModelGenerator(obj._meta.model, view, overwrite=True)
    g.obj_create(obj)

def file_static_delete(obj, view):
    '''
    Preconfigured Filesystem delete.
    PK for id.
    '''
    g = ModelGenerator(obj._meta.model, view)
    g.obj_delete(obj)
