from django.core.management.base import BaseCommand, CommandError
from static_models.view_generator import ViewStaticManager
#from static_models.settings import settings
from django.conf import settings




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
        if (not('view' in vs)):
            vs['view'] = None
        if (not('query' in vs)):
            vs['query'] = None
        if (not('urls' in vs)):
            vs['urls'] = []
        if (not('filename' in vs)):
            vs['filename'] = None
        if (not('filename_from_attribute' in vs)):
            vs['filename_from_attribute'] = 'pk'
        if (not('filepath' in vs)):
            vs['filepath'] = None
        return vs

                    
    def handle(self, *args, **options):         
        extension = ''
        if (options['html_extension']):
            extension = 'html'

        # first check this
        # This is an error not attepted to default
        try:
            settings.STATICVIEWS_DIR
        except AttributeError:
            raise CommandError('The static_models app requires a setting STATICVIEWS_DIR to be defined.')

        valid_entries = []
        for e in settings.STATIC_VIEWS:
            if (not (e.get('urls')) and not (e.get('view'))):
                self.stdout.write(
                    f'WARNING: The static_models app requires settings STATIC_MODELVIEWS entriies to have a "view" pt "urls" key. entry:{e}'
                )
            else:
                valid_entries.append(e)                
        normalised_entries = [self.normalize_viewsetting(e) for e in valid_entries]
            
        # ok, generate
        count = 0

        if (options['sync'] and (options['verbosity'] > 0)):
            self.stdout.write(
                "Info: Directories will be cleared before generation"
            )        
            
        # This is defended to do as much as possible
        for vs in normalised_entries:
            g = None
            try:
                g = ViewStaticManager(
                    vs['view'],
                    vs['query'], 
                    vs['urls'],
                    vs['filename'],
                    vs['filename_from_attribute'],
                    vs['filepath'],
                    overwrite=options['overwrite'],
                    extension=extension,
                )
            except Exception as ex:
                self.stdout.write(
                    f"Fail report: {ex}"
                )  
                self.stdout.write(
                    f"WARNING: Data from a setting failed. setting{vs}"
                )    
            if g:
                delete_count = 0
                if (options['sync']):
                    delete_count = g.delete()
                    
                count = g.create()
                if (options['verbosity'] > 0):
                    print("{} static file(s) created at '{}'".format(count, g.location))
