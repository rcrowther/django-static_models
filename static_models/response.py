import os
from django.http.response import FileResponse
from django.core.exceptions import ImproperlyConfigured


class AssuredFileResponse(FileResponse):
    """
    A streaming HTTP response class optimized for files.
    Differs from FileResponse because it assumes the file is what the 
    respose has been told it is, as content_type. No guesses. So you
    would have to set, for example 'application/gzip' for zipped files.
    """
    def __init__(self, *args, content_type=None, **kwargs):
        if content_type is None:
            raise ImproperlyConfigured(
                "AssuredFileResponse requires an attribute 'content_type'"
                " passed in initial parameters")
        super().__init__(*args, content_type=content_type, **kwargs)

    def set_headers(self, filelike):
        """
        Set some common response headers (Content-Length, Content-Type, and
        Content-Disposition) based on the `filelike` response content.
        """
        # encoding_map = {
            # 'bzip2': 'application/x-bzip',
            # 'gzip': 'application/gzip',
            # 'xz': 'application/x-xz',
        # }
        filename = getattr(filelike, 'name', None)
        filename = filename if (isinstance(filename, str) and filename) else self.filename
        if os.path.isabs(filename):
            self['Content-Length'] = os.path.getsize(filelike.name)
        elif hasattr(filelike, 'getbuffer'):
            self['Content-Length'] = filelike.getbuffer().nbytes

        # if self.get('Content-Type', '').startswith('text/html'):
            # if filename:
                # content_type, encoding = mimetypes.guess_type(filename)
                # # Encoding isn't set to prevent browsers from automatically
                # # uncompressing files.
                # content_type = encoding_map.get(encoding, content_type)
                # self['Content-Type'] = content_type or 'application/octet-stream'
            # else:
                # self['Content-Type'] = 'application/octet-stream'
                        
        filename = self.filename or os.path.basename(filename)
        if filename:
            disposition = 'attachment' if self.as_attachment else 'inline'
            try:
                filename.encode('ascii')
                file_expr = 'filename="{}"'.format(filename)
            except UnicodeEncodeError:
                file_expr = "filename*=utf-8''{}".format(quote(filename))
            self['Content-Disposition'] = '{}; {}'.format(disposition, file_expr)
        elif self.as_attachment:
            self['Content-Disposition'] = 'attachment'
            

