from django.core.management.base import BaseCommand, CommandError
from static_models.view_generator import ViewStaticManager
from static_models.settings import settings




class Command(BaseCommand):
    help = 'Create/update static files'
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help="Before generation, delete existing files.",
        )
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

    def normalize_viewsetting(self, vs):
        if (not('query' in vs)):
            vs['query'] = None
        if (not('urls' in vs)):
            vs['urls'] = []
        if (not('filename' in vs)):
            vs['filename'] = None
        if (not('filename_from_field' in vs)):
            vs['filename_from_field'] = 'pk'
        if (not('filepath' in vs)):
            vs['filepath'] = None


                    
    def handle(self, *args, **options):         
        extension = ''
        if (options['html_extension']):
            extension = 'html'
        normalised_viewsettings = [self.normalize_viewsetting(vs) for vs in settings.modelviews]

        # ok, generate
        count = 0

        if (options['sync'] and (options['verbosity'] > 0)):
            print("Directories will be cleared before generation")
                    
        for vs in settings.modelviews:
            g = ViewStaticManager(
                vs['view'],
                vs['query'], 
                vs['urls'],
                vs['filename'],
                vs['filename_from_field'],
                vs['filepath'],
                overwrite=options['overwrite'],
                extension=extension,
            )
            
            delete_count = 0
            if (options['sync']):
                delete_count = g.delete()
                
            count = g.create()
            if (options['verbosity'] > 0):
                print("{} static file(s) created at '{}'".format(count, g.location))
