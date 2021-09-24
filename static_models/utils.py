from django.apps import apps
from django.core.exceptions import ImproperlyConfigured


#! unused?
def get_model(model_path):
    Model = None
    if (model_path):
        model_path_elements = model_path.split('.', 1)
        if (len(model_path_elements) != 2):
            raise ImproperlyConfigured("Unable to parse model path (must be form 'app.model'): '{}'".format(model_path))        
        an = model_path_elements[0]
        mn = model_path_elements[1]
        try:
            Model = apps.get_model(an, mn)
        except Exception as e:
            raise ImproperlyConfigured("Unable to locate model from path: '{}'".format(model_path))
    return Model
