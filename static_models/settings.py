from django.conf import settings as dsettings
from django.core.exceptions import ImproperlyConfigured
from static_models import utils
from django.utils import module_loading


        
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
        self.staticmodels_dir = None
        self.modelviews = []
        if (not self.staticmodels_dir):
            self.populate()
                 
    def populate(self):
        if (not(hasattr(dsettings, 'STATICMODELS_DIR'))):
            raise ImproperlyConfigured('The static_models app requires STATICMODELS_DIR to be defined in settings.')
        self.staticmodels_dir = dsettings.STATICMODELS_DIR
            
        if (hasattr(dsettings, 'STATIC_MODELVIEWS')):
            modelviews = dsettings.STATIC_MODELVIEWS
            self.modelviews = self.build_modelviews(modelviews)

    def build_modelviews(self, modelviews):
        b = []
        for mv in modelviews:
            model = mv['model']
            if not isinstance(model, list):
                # given modelname, check model exists
                model = utils.get_model(model)

            # test existance of a view?
            viewwname = mv['view']
            view = module_loading.import_string(viewwname)
            id_fieldname = 'pk'
            if ('id_fieldname' in mv):
                id_fieldname = mv['id_fieldname']
            pathroot = ''
            if ('pathroot' in mv):
                pathroot = mv['pathroot']
            b.append((model, view, id_fieldname, pathroot))
        return b
            
    def __repr__(self):
        return "Settings(staticmodels_dir:{}, modelviews:{})".format(
            self.staticmodels_dir,
            self.modelviews,
        )

# set one up
settings = Settings()
