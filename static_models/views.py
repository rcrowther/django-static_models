import posixpath
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import View
from django.http import (
    Http404, HttpResponseNotModified,
)
from django.utils._os import safe_join
from django.utils.translation import gettext as _, gettext_lazy
from static_models.response import AssuredFileResponse
from django.views.static import was_modified_since
from django.utils.http import http_date



#! Probably needs a alternate id field slector
class StaticResponseMixin:
    #NB this is a muddle of DetailView, other base view code, and 
    # impatience with Django twaddle. 
    path_root=None

    def __init__(self, **kwargs):   
        kwargs['content_type'] ='text/html' 
        super().__init__(**kwargs)

        #NB TemplateResponseMixin uses late call to check path_root not None.
        # Flexible, but weedy. Define by init, or error.
        if self.path_root is None:
            raise ImproperlyConfigured(
                "StaticView requires an attribute 'path_root'"
                " which can be defined, or passed in initial parameters")

    def get_id_path(self):
        id_path=None
        pk = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')
        path = self.kwargs.get('path')
        
        # start with pk
        if (pk is not None):
            id_path = str(pk)

        # try slug.
        if (slug is not None and (pk is None)):
            id_path = str(slug)

        # try path
        if ((pk is None) and (slug is None) and path is not None):
            id_path = str(path)
                    
        # If nothing defined, error.
        if (not id_path):
            raise AttributeError(
                "StaticView %s must be called with a "
                "parameter named 'pk', 'slug' or 'path' in the URLconf." % self.__class__.__name__
            )            
        return id_path #+ '.html'

    def get_fullpath(self):
        #NB split out so you could, say, implement a 'delete' method on 
        # a view
        return Path(safe_join(self.path_root + self.get_id_path()))
    
    def render_to_response(self, **response_kwargs):
        '''
        Use class data to make a Django HTTP response.
        Would only in most universes be implemented on 'get'
        '''
        #NB some code here comes from django.views.static
        fullpath = self.get_fullpath()
        
        # Respect the If-Modified-Since header.
        statobj = fullpath.stat()
        if not was_modified_since(self.request.META.get('HTTP_IF_MODIFIED_SINCE'),
                                  statobj.st_mtime, statobj.st_size):
            return HttpResponseNotModified()
        try:
            f = fullpath.open('rb')
        except FileNotFoundError:
            raise Http404(_('“%(path)s” does not exist') % {'path': fullpath})

        response = AssuredFileResponse(
            f,
            as_attachment=False,
            content_type='text/html',
            **response_kwargs
        )
        response["Last-Modified"] = http_date(statobj.st_mtime)
        return response
            
            
            
class StaticView(StaticResponseMixin, View):
    '''
    Render a static file.
    Acts on URL parameters 'pk' or 'slug'.
    
    path_root
        Path to a directory of files used as response data. You may want
        to set with settings.MEDIA_ROOT, but this class has no opinion.
    '''       
    def get(self, request, *args, **kwargs):
        return self.render_to_response()
