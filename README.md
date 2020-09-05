# django-static-models
Generate static pages from a Django app. Works from the models, put the results in a directory.

Has no deployment code. Deployment is assumed to be a seperate step, and your business (and maybe trouble).

## What this app is and is not
Because most websites include some static files, the word ''static' has many uses,

This app generates pages from the app models in a Django site. This is mainly intended for creating a site where the deployed content is partially or fully static. Such a site will not have dynamic facilities such as logons or personalisation. But it will be fast, easy to deploy and, in terms of conventional concerns, have few security issues. 

It should be noted that some dynamic facilities can still be added to such a site, using external services. Email handling, shopping, and search can be created using links to external sites. Javascript can be used to inject tailored information. Or Django can be enabled where necessary---if a site can function without logons, but needs a search, Django can be deployed without Admin. 

This app is not for supplementing Django's existing tools for handling of static resources. Nor is it specifically for optimizing output. It is for generating pages from models, where those pages have no (or scripted) dynamic behaviour.


## Quickstart
Quickstart is not a good name as there is no quick start here. You need a model and a view, typically a DetailView or like, to work with.

Generate some pages,

    ./manage.py -o modelstaticmerge pathToSomeModel pathToSomeView

[Serve them](#through-Django-url-config) through the buitin URL config


## Overview
This being Django, the action is not as simple as it sounds. What the app does is generate q request response, which in Django is an encoded stream, then writes the contents to storage, with a filename built from a pk.

There are some considerations with this. A file with a non-html extension [can not be served through Django servers](#serving-files) (they are treaded as download streams). 

The main code is in 'static_models.utils.ModelGenerator', which is well-documented. If you need something different, try look there.

  
## Management commands
Typically,

    ./manage.py -o modelstaticmerge pathToSomeModel pathToSomeView

The 'overwrite' option prevents renaming, which is the default.

The management command is deliberately stripped down. You can do the same, with more options, by using the shell to import the ModelGenerator class from static_models.utils. 
 

## Generating pages
The app must be told where to put generated files. Variations of location can be configured,

    model only
        Paths are ''base_path + model_name + id'. 'id' is by default the pk. This solution can only handle one set of pages per app, which would usually correspond to a DetailView. That said, the results are simple, e.g. ''.../media/site/appname/7'

    model and view
        Include the view name, which allows several views per app. Not as obvious, but flexibile e.g. ''.../media/site/appname/viewname/7'


## Maintaining static pages
How can the static page stock be maintained if content is changed? One way is to run a maintenance command periodically. If you want to merge automatically, there's a few ways, none are wonderful. I'd favour using the post_save signal in 'apps.py'. That will work with all model changes, and contains the logic within the app,

To auto-merge filesystem storage,

    def static_merge(sender, instance=None, **kwargs):
        from image.views import ArticleDetailView
        from static_models.utils import file_static_merge
        file_static_merge(instance, ArticleDetailView)

    class ImageConfig(AppConfig):
        ...
        def ready(self):
            ...
            from django.db.models.signals import post_save
            from image.models import Page
            post_save.connect(static_merge, sender=Page)

For more options, run full static handling,

    def static_merge(sender, instance=None, **kwargs):
        from article.views import ArticleDetailView
        from static_models.utils import ModelGenerator
        g = ModelGenerator(sender, ArticleDetailView, overwrite=True)
        g.obj_create(instance)

    class ImageConfig(AppConfig):
        ...
        def ready(self):
            ...
            from django.db.models.signals import post_save
            from article.models import Page
            post_save.connect(static_merge, sender=Page)


g.obj_delete() can be used in the same way on post_delete, but be careful if you want to share the static pages, that you do not delete data expected elsewhere.
 
## Serving files
The generated pages will have correct internal links ie. for resources like CSS or image links.

### As true static
One way to use the pages is to transfer the filetree to /static and let the static server take over. This is super-cool deployment.

There is an issue or two with this. For security reasons, Django storage devices will refuse to write pages into the /static directory. So I'm not overriding, even for maintenance work. You need to transfer the files by hand, or make some external dev automation. 

Also, the Django dev server will not recognise pages that do not have an 'htm'/'html' extension. It will serve them as data streams. The generator allows you to put an 'html' extension on pages, but then URL links to the page will fail. There are all sorts of server/link fixes, or you may not care about dev viewing. If you are interested in this approach, you'll need to look at your server configuration.


### Through Django URL config
Another way to serve pages is to use Django URL configuration. This has the disadvantage of not being as clean as fully static pages, and some Django must remain. The advantage is you can configure URLs as you wish, and integrate with other Django using a similar API to dynamic page building. Put this (or something similar) in ''urls.py',

    from django.conf import settings
    from static_models.views import StaticView
        ...
        path('image2/<int:pk>/', StaticView.as_view(path_root= settings.MEDIA_ROOT + '/site/article/'), name='image2-detail'),

This code uses MEDIA_ROOT. StaticView has no opinion on the pathstyle.

You can define path_root using a custom class declaration, With that you can configure fancy URL resolution/HTTP responses etc. e.g.

    from django.conf import settings
    from static_models.views import StaticView

    class ArticleStaticView(StaticView):
        path_root = settings.MEDIA_ROOT + '/site/article/'
        ...

And in ''urls.py',

    from article.views import ArticleStaticView
        ...
        path('image2/<int:pk>/', ArticleStaticView.as_view(), name='image2-detail'),

 

## Alternatives
You could use some outside tool to grab pages directly from the server, in the same way a web-cache like Squid works.

Closer to the codebase, Wagtail CMS have been [talking about using Gatsby](https://wagtail.io/blog/using-gatsby-wagtail-build-case-study/) for the purpose of storing static pages.

[Deploy Django without admin](https://stackoverflow.com/questions/4845239/how-can-i-disable-djangos-admin-in-a-deployed-project-but-keep-it-for-local-de). No logons then, of course, but removes many potential security violations while allowing dynamic templates and form-handling. 

[django-static-sites](https://github.com/ciotto/django-static-sites/tree/master/staticsites) 
    Deployment options built in. 

[django-static-delivery 0.0.1](https://pypi.org/project/django-static-delivery/) 
    A middleware solution, which makes sense. Probably more of an optimiser than a generator, but untested.

[django-static-pages](https://pypi.org/project/django-static-pages/)
    Uses test client to generate pages, Not clear if it is only for testing?

