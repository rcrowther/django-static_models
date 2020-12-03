from django.core.management.base import BaseCommand, CommandError
#from django.utils import module_loading
from static_models.model_generator import ModelManager
from static_models.settings import settings




class Command(BaseCommand):
    help = 'Create/update static files'
        
    def add_arguments(self, parser):
        #common.add_model_argument(parser)
        #parser.add_argument('view', type=str)
        # common.add_contains_argument(parser)
        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            help="Replace currently existing files (default is to ignore)",
        )
        parser.add_argument(
            '-e',
            '--html_extension',
            action='store_true',
            help="Add '.html' extension to generated files.",
        )

    def handle(self, *args, **options):         
        extension =  None
        if (options['html_extension']):
            extension = 'html'
             
        # ok, generate
        count = 0
        for (Model, View, id_fieldname, pathroot) in settings.modelviews:
            g = ModelManager(
                Model, 
                View,
                pathroot=pathroot,
                overwrite=options['overwrite'],
                id_fieldname=id_fieldname,
                extension=extension,
            )

            count = g.all_create()

            if (options['verbosity'] > 0):
                print("{} static file(s) created at '{}'".format(count, g.location))
