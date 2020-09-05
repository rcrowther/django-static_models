import unittest
from django.test import TestCase
from static_models.utils import ModelGenerator


# ./manage.py test static_models.tests.test_generate
class TestGenerate(TestCase):
    
    def setUp(self):
        #! need to create a model to work on
        
        # self.generator = ModelGenerator(
            # model,
            # view,
            # storage=FileSystemStorage,
            # overwrite=True,
            # path_includes_view=False,
            # slug_in_path=False,
            # extension=None,
        # )
        pass
