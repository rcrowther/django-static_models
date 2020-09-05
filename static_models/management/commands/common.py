from django.core.management.base import CommandError
from django.apps import apps

def add_model_argument(parser):
        parser.add_argument('model', type=str)

def get_model(options):
    model_path = options['model']
    model_path_elements = model_path.split('.', 1)
    if (len(model_path_elements) != 2):
        raise CommandError("Unable to parse model path (must be form 'app.model'): '{}'".format(model_path))        
    an = model_path_elements[0]
    mn = model_path_elements[1]
    try:
        Model = apps.get_model(an, mn)
    except Exception as e:
        raise CommandError("Unable to locate model from path: '{}'".format(model_path))
    return Model
