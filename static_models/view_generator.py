import os
import re
import pathlib
from django.conf import settings
from django.http.request import HttpRequest, QueryDict
from django.core.files.base import ContentFile
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils import module_loading
from pathlib import Path
from urllib.parse import urlparse


from django.core.handlers.wsgi import WSGIRequest
from io import BytesIO
from urllib.parse import unquote_to_bytes, urljoin, urlparse, urlsplit
from django.utils.encoding import force_bytes
from django.utils.http import urlencode
from django.core.servers.basehttp  import get_internal_wsgi_application


    
                    
class RequestFactory:
    # Build a mocked up request
    # hacked out of django.test.clients
    def __init__(self):
        #self.json_encoder = json_encoder
        #self.defaults = defaults
        #self.cookies = SimpleCookie()
        self.errors = BytesIO()
        
    def _base_environ(self, **request):
        """
        The base environment for a request.
        """
        # This is a minimal valid WSGI environ dictionary, plus:
        # - HTTP_COOKIE: for cookie support,
        # - REMOTE_ADDR: often useful, see #8551.
        # See https://www.python.org/dev/peps/pep-3333/#environ-variables
        return {
            'HTTP_COOKIE': '',
            'PATH_INFO': '/',
            'REMOTE_ADDR': '127.0.0.1',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            # Pretend on localhost, like the development it is
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            #'wsgi.input': FakePayload(b''),
            'wsgi.input':            BytesIO(),
            'wsgi.errors': self.errors,
            'wsgi.multiprocess': True,
            'wsgi.multithread': False,
            'wsgi.run_once': False,
            #**self.defaults,
            **request,
        }

    def request(self, **request):
        "Construct a generic request object."
        return WSGIRequest(self._base_environ(**request))

    def generic(self, method, path, data='',
                content_type='application/octet-stream', secure=False,
                **extra):
        """Construct an arbitrary HTTP request."""
        parsed = urlparse(str(path))  # path can be lazy
        data = force_bytes(data, settings.DEFAULT_CHARSET)
        r = {
            'PATH_INFO': self._get_path(parsed),
            'REQUEST_METHOD': method,
            'SERVER_PORT': '443' if secure else '80',
            'wsgi.url_scheme': 'https' if secure else 'http',
        }
        # if data:
            # r.update({
                # 'CONTENT_LENGTH': str(len(data)),
                # 'CONTENT_TYPE': content_type,
                # 'wsgi.input': FakePayload(data),
            # })
        ##r.update(extra)
        # If QUERY_STRING is absent or empty, we want to extract it from the URL.
        if not r.get('QUERY_STRING'):
            # WSGI requires latin-1 encoded strings. See get_path_info().
            query_string = parsed[4].encode().decode('iso-8859-1')
            r['QUERY_STRING'] = query_string
        return self.request(**r)

    def _get_path(self, parsed):
        path = parsed.path
        # If there are parameters, add them
        if parsed.params:
            path += ";" + parsed.params
        path = unquote_to_bytes(path)
        # Replace the behavior where non-ASCII values in the WSGI environ are
        # arbitrarily decoded with ISO-8859-1.
        # Refs comment in `get_bytes_from_wsgi()`.
        return path.decode('iso-8859-1')

    def get(self, path, data=None, secure=False, **extra):
        """Construct a GET request."""
        data = {} if data is None else data
        return self.generic('GET', path, secure=secure, **{
            'QUERY_STRING': urlencode(data, doseq=True),
            **extra,
        })
       
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
    filename_from_attribute
        For use on models. The value from this fieldname is used to 
        provide the filename. Most likely targets a slugfield. Can also
        build from zero-attribute callables. Default is 'pk'
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
        view = None,
        query = None,
        urls = [],
        filename = None,
        filename_from_attribute ='pk',
        filepath = None,
        overwrite = False,
        extension = '',
    ):
        if isinstance(view, str): 
            view = get_view(view)
        self.View = view

        self.basepath = Path(settings.STATICVIEWS_DIR)

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
        if (urls):
            # If there are URLs to process, start an internal server.
            # This server is like the one run by ''runserver'
            # Radically this is a BaseHandler, set with the local 
            # environment. AFAIK, it needs no closure. Also, errors
            # it throws are natural and good as they read.
            self.server = get_internal_wsgi_application()
        
        self.overwrite = overwrite
        self.filename = filename
        self.filename_from_attribute = filename_from_attribute
        self.id_fieldname = filename_from_attribute


                    
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

        # get a context
        # nearly all views have a context, but the base doesn't. So...
        ctx = {}
        if (hasattr(view, 'get_context_data')):
            ctx = view.get_context_data()

        # get and render response
        count = 0
        response = view.render_to_response(ctx)        
        r = self.render(response, full_filepath)
        if(r):
            count = 1
        return count

####
    def filename_from_url(self, url):
        # Attempt to make a filename from a URL
        # Try for a query, a fragment, then last part of path 
        urlparts = urlparse(url)
        fid = ""
        if (urlparts.query or urlparts.fragment):
            query = ''
            if (urlparts.query):
                query = '?' + urlparts.query
            fragment = ''
            if (urlparts.fragment):
                fragment = '#' + urlparts.fragment
            fid = query + fragment
        if not(fid):
            #! Not good enough. Different no last slash/slash
            path = urlparts.path
            if (path[-1] == "/"):
                path = path[0 : -1]
            path = path.rsplit('/', 1)
            if (path):
                fid = path[-1]
        if not(fid):
            raise ImproperlyConfigured(f'Cannot construct an identifier from given URL. name:"{url}"')
        return fid

    # At some point, angling for this to be the method for view-writing 
    # also
    def writeContent(self, content, full_filepath):
        isfile = full_filepath.is_file()         
        size = 0
        if(isfile):
            size = os.path.getsize(full_filepath)
        generated_size = len(content)
        if ((generated_size != size) or self.overwrite):
            with open(full_filepath, 'wb') as fd:  
                fd.write(content) 
            return full_filepath
        return None
        
    def create_from_url(self, url_filename):
        url = url_filename[0]
        fid = url_filename[1]
        if (fid is None):
            fid = self.filename_from_url(url)
            
        # make the full filepath
        full_filepath = self.filepath / (fid + self.extension)

        # Only request a rough filepath in settings. So a very basic
        # normalisation that the filepath is absolute to site base 
        if (url[0] != '/'):
            url = '/' + url
            
        # Generate a mock request
        # Needs to be a different level of handling because the only 
        # data is a URL, no object to root out context etc.
        # So go high, ask a test server
        rf = RequestFactory()
        wsgiRequest = rf.get(url)

        # For a response, run through the server
        httpResponse = self.server.get_response(wsgiRequest)
        
        # get content and write to file
        content = httpResponse.content
        return self.writeContent(content, full_filepath)

    def render_urls(self, urls):
        count = 0
        for url_filename in urls.items():
            r = self.create_from_url(url_filename)
            if (r):
                count += 1 
        return count

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
        fid = getattr(obj, self.filename_from_attribute) 
        if callable(fid):
            fid = fid()
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
        if (self.urls):
            return self.render_urls(self.urls)
        if (self.query):
            return self.render_query_set(self.View, self.query)
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
