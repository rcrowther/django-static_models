from django.core.management.base import BaseCommand, CommandError
from django.utils import module_loading
from . import common
from static_models.utils import ModelGenerator 



class Command(BaseCommand):
    help = 'Create/update static files'
        
    def add_arguments(self, parser):
        common.add_model_argument(parser)
        parser.add_argument('view', type=str)
        # common.add_contains_argument(parser)
        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            help="Replace currently existing files (default is to rename)",
        )
        parser.add_argument(
            '-e',
            '--html_extension',
            action='store_true',
            help="Add '.html' extension to generated files.",
        )

    def handle(self, *args, **options):
        Model = common.get_model(options)
                
        view_path = options['view']

        try:
            View = module_loading.import_string(view_path)
        except ValueError:
            raise CommandError("Unable to split path: path:'{}'".format(view_path))
        except (AttributeError, ImportError):
            split_path = view_path.rsplit('.', 1)
            raise CommandError("Unable to locate view in module. module:'{}' view:'{}'".format(
            split_path[0],
            split_path[1]
            ))           
            
        extension =  None
        if (options['html_extension']):
            extension = 'html'
             
        # ok, generate
        g = ModelGenerator(
            Model, 
            View,
            overwrite=options['overwrite'],
            extension=extension,
        )
        count = g.all_create()

        if (options['verbosity'] > 0):
            print("{} static file(s) created at '{}'".format(count, g.location))
