from django.conf import settings as dsettings
from django.core.exceptions import ImproperlyConfigured
from django.utils import module_loading


#! Generally deprecated, in favour of a few checks
class Settings():
    '''
    Gather settings from the settings file.
    For easy access and maybe caching. Django enables attribute access 
    on the Settings.py file, but it is awkward poking in for app-related
    settings.
    
    app_dirs 
        if true, seek for image filters in registtered apps
    modules 
        module paths to seek image_filters modules 
    '''
    def __init__(self):
        # defaults
        self.STATICVIEWS_DIR = None
        self.modelviews = []
        if (not self.STATICVIEWS_DIR):
            self.populate()
                 
    def populate(self):
        if (not(hasattr(dsettings, 'STATICVIEWS_DIR'))):
            raise ImproperlyConfigured('The static_models app requires a setting STATICVIEWS_DIR to be defined.')
        self.staticviews_dir = dsettings.STATICVIEWS_DIR
            
        if (hasattr(dsettings, 'STATIC_VIEWS')):
            viewsettings = dsettings.STATIC_VIEWS
            self.modelviews = self.build_viewsettings(viewsettings)

    def check_viewsetting(self, vs):
        #if (not ('data' in vs or 'urls' in vs)):
        #    raise ImproperlyConfigured(f'The static_models app requires settings STATIC_MODELVIEWS entires to have a "data" or "urls" key (the key can be empty). entry:{vs}')
        #if (('data' in vs) and not (isinstance(vs['data'], dict))):
        #    raise ImproperlyConfigured(f'The static_models app setting STATIC_MODELVIEWS "data" key is not a dict. entry:{vs}')
        if (not ('urls') and not ('view' in vs)):
            raise ImproperlyConfigured(f'The static_models app requires settings STATIC_MODELVIEWS entriies to have a "view" pt "urls" key. entry:{vs}')
                         
                         
    def build_viewsettings(self, viewsettings):
        b = []
        for mv in viewsettings:
            self.check_viewsetting(mv)

            # test existance of a view?
            # in management or generator?
            if ('view' in mv):
                viewname = mv['view']
                try:
                    view = module_loading.import_string(viewname)
                except ImportError:
                    #print(repr(view))
                    raise ImproperlyConfigured(f'View not visible to a module loader. entry:{viewname}')
                    
            b.append(mv)
        return b
            
    def __repr__(self):
        return "Settings(staticviews_dir:{}, modelviews:{})".format(
            self.staticviews_dir,
            self.modelviews,
        )

# set one up
settings = Settings()
