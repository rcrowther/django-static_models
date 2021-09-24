import os
import re
import pathlib
#from django.conf import settings
from django.conf import settings as dsettings

from django.http.request import HttpRequest, QueryDict
from django.core.files.base import ContentFile
from static_models.settings import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils import module_loading
from pathlib import Path
from urllib.parse import urlparse


def get_view(viewname):
    '''
    Return a view class.
    viewname
        a path and viewname, as string
    '''
    try:
        view = module_loading.import_string(viewname)
    except ImportError:
        raise ImproperlyConfigured(f'View not visible to a module load. name:"{viewname}"')
    return view


                    
class ViewStaticManager():
    '''
    Generate static files from a Model.
    
    If the data is a model it should not be an instance. The code will 
    assume the view is generic and set the model.
    If the data is a list of dicts the code will pass each dict to the 
    view context.  
    In both cases, the id of the object, and so the filename, will be 
    taken from id_fieldname.
    view
        Must be at least a DetailView. Either a string path or the View 
        class (but not an instance).
    query
        For a model. Currently, only 'all' is accepted. 
    urls
        List of IRLs to evoke the View.
    filename
        A name for one-off view evokation.
    filename_from_field
        The value from this fieldname is used to provide the filename.
        Most likely targets a slugfield. Default is 'pk'
    filepath
        Path from the configured rootdir to the output of this class.
        If empty, the pathroot is empty, unless the data is a model,
        in which case it defaults to a modelname and opetional 
        viewname.
    overwrite
        overwrite existing generated files, even if same size. Default 
        is False.
    extension
        Optional extension name. Dot is added automatically.
    '''
    #! reorder
    def __init__(self, 
        view,
        query=None,
        urls=[],
        filename=None,
        filename_from_field='pk',
        filepath=None,
        overwrite=False,
        extension='',
    ):
        if isinstance(view, str): 
            view = get_view(view)
        self.View = view

        self.basepath = Path(dsettings.STATICVIEWS_DIR)

        # decide a path from the configured dir to this view output
        self.filepath = self.get_filepath(
            self.basepath,
            filepath, 
            self.View
        )
        
        # make the destination dirs
        self.filepath.mkdir(exist_ok=True)
        
        # set extension
        if (extension):
            extension = '.' + extension        
        self.extension = extension
                      
        self.query = query
        self.urls = urls
        self.overwrite = overwrite
        self.filename = filename
        self.filename_from_field = filename_from_field
        self.id_fieldname = filename_from_field


                    
    def get_filepath(self, basedirpath, filepath, view):
        '''
        return 
        The path if given. If not, and a view model exists, use the 
        model name. If the view is not a model, return a default of no 
        path 
        ''' 
        if ((filepath is None) and hasattr(view, 'model')):
            modelname = view.model._meta.model_name
            filepath = self.camelcase_to_underscore(modelname)
        if (filepath is None):
            filepath = ''
        return basedirpath / filepath

    def mk_request(self, url=''):
        request = HttpRequest()
        
        #! need to minimally populate this       
        #- how fragment/query into GET?
        urlparts = urlparse(url)
        querystring = urlparts.query #+ urlparts.fragment
        request.GET = QueryDict(querystring)
        request.path = urlparts.path
        request.method = 'GET'
        return request         
        
    @property
    def location(self):
        '''
        Return a human readable location for the files.
        For display, not good for code.
        return
            The path relative to django base, plus whatever further path 
            decided.
        '''
        return self.filepath.relative_to(self.basepath.parent)
                
    def camelcase_to_underscore(self, s):
        # A utility for generating a filename from view classes
        # Lifted from someplace in Django?
        # https://djangosnippets.org/snippets/585/
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s).lower().strip('_')

####
    def render_no_input(self, View, filename):
        if (not(filename)):
            raise ImproperlyConfigured('If no "query" or "url" attribute, then a filename is required')

        # could only be one file?
        full_filepath = self.filepath / (filename + self.extension)
        
        # make a view
        view = View()

        # can be a boring generic request for now.
        view.request = self.mk_request()
        ctx = {}
        count = 0
        response = view.render_to_response(ctx)        
        r = self.render(response, full_filepath)
        if(r):
            count = 1
        return count

####
    def render_urls(self, View, urls):
        count = 0
        for url_filename in urls.items():
            r = self.create_from_url(View, url_filename)
            if (r):
                count += 1 
        return count

    def filename_from_url(self, url):
        urlparts = urlparse(url)
        if (urlparts.query or urlparts.fragment):
            query = ''
            if (urlparts.query):
                query = '?' + urlparts.query
            fragment = ''
            if (urlparts.fragment):
                fragment = '#' + urlparts.fragment
            fid = query + fragment
        if not(fid):
            fid = urlparts.path.rsplit['/', 1][0]
        if not(fid):
            raise ImproperlyConfigured(f'Cannot construct an identifier from given URL. name:"{url}"')
        return fid
        
    def create_from_url(self, View, url_filename):
        url = url_filename[0]
        fid = url_filename[1]
        if (fid is None):
            fid = self.filename_from_url(url)
            
        # make the full filepath
        full_filepath = self.filepath / (fid + self.extension)

        # Tune up view with request
        request = self.mk_request(url)
        as_view = View.as_view() 
        response = as_view(request) #, *args, **kwargs)
        return   self.render(response, full_filepath)

                                                
    def render_query_set(self, View, query='all'):
        view = View()
        if (query == 'all'):
            qs = view.model.objects.all()
        else:
            qs = view.model.objects.filter(query)
            
        count = 0
        for obj in qs: 
            r = self.create_from_obj(view, obj)
            if (r):
                count += 1 
        return count
                
    def create_from_obj(self, view, obj):
        fid = getattr(obj, self.filename_from_field) 
        full_filepath = self.filepath / (fid + self.extension)
        view.object = obj

        # can be a boring generic request for now.
        view.request = self.mk_request()
        ctx = view.get_context_data()
        response = view.render_to_response(ctx)
        return self.render(response, full_filepath)
        
    def render(self, response, full_filepath):
        '''
        Resder the response o a file
        only if sizes match, or override is set.
        '''
        isfile = full_filepath.is_file() 
        
        size = 0
        if(isfile):
            size = os.path.getsize(full_filepath)
        
        # Response only caches data, resolve
        rr = response.render()
        
        # Gets the data itself
        #! still bytes
        #! where stripped?
        cf = ContentFile(rr.content, name=None)
        generated_size = cf.size
        if ((generated_size != size) or self.overwrite):
            with open(full_filepath, 'wb') as fd:  
                fd.writelines(cf.open())  
            return full_filepath
        return None

    def create(self):
        if (self.query):
            return self.render_query_set(self.View, self.query)
        if (self.urls):
            return self.render_urls(self.View, self.urls)
        return self.render_no_input(self.View, self.filename)

    def delete(self):
        '''
        Delete existing generated files.
        Crude, simply clears the target directory. Will not clear the
        directory itself, nor subdirectories.
        '''
        count = 0
        for path in self.filepath.iterdir():
            # The app can generate a nested directory structure. IT is
            # possible a general delete will find a nested directory.
            # We do not want to delete that, as it may not be requested
            # by the user. So gently as psssible, exceptions are quietly 
            # ignored
            r = None
            try:
                r = path.unlink(missing_ok=True)
            except:
                pass
            if (r):
                count += 1
        return count
        
        

        
def file_static_merge(obj, view):
    '''
    Preconfigured Filesystem save.
    PK for id and overwriting.
    '''
    g = ViewStaticManager(obj._meta.model, view, overwrite=True)
    g.obj_create(obj)

def file_static_delete(obj, view):
    '''
    Preconfigured Filesystem delete.
    PK for id.
    '''
    g = ViewStaticManager(obj._meta.model, view)
    g.delete(obj)
