from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StaticModelsConfig(AppConfig):
    name = 'static_models'
    verbose_name = _("Generate static pages from models")
