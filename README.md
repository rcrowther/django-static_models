# django-static-models
> :warning: **If you have tried this app** The configuration targeting has changed completely. The app has moved away from using Django storage, which is for unsafe material, to fixed configuration through 'settings.py'.

Generate static pages from a Django app. Despite the name, can generate from most views, then puts the results in a directory.

Has no deployment code. Deployment is assumed to be a separate step, and your business (and maybe trouble).

## What this app is and is not
Because most websites include some static files, the word ''static' has many uses,

This app generates pages from the views in a Django site. This is mainly intended for creating a site where the deployed content is partially or fully static. Such a site will not have dynamic facilities such as logons or personalisation. But it will be fast, easy to deploy and, in terms of conventional concerns, have few security issues. 

It should be noted that some dynamic facilities can still be added to such a site, using external services. Email handling, shopping, and search can be created using links to external sites. Javascript can be used to inject tailored information. Or Django can be enabled where necessary---if a site can function without logons, but needs a search, Django can be deployed without Admin. 

This app is not for supplementing Django's existing tools for handling of static resources. Nor is it specifically for optimizing output. It is for generating pages from models, where those pages have no (or scripted) dynamic behaviour.

## Why you may or may not use it
Pros,
- You want static pages from a Django project output
- Simple. Add some configuration

Cons,
- No middleware solution. So generated pages are not deployed in the running app (though you can view them directly)
- Deploy is not considered

## Quickstart
Quickstart is not a good name as there is no quick start here. You need a model and a view, typically a DetailView or like, to work with.

- Set a config
- Generate some pages './manage.py -o modelstaticmerge' 
- Look in the 'site/' folder in the top level of the project,


## Overview
The main work is in the config, which describes which views are served with what data, and where the generated pages are to be written.

This being Django, the action is not as simple as it sounds. What the app does is generate an HTML response, which in Django is an encoded stream, then writes the contents to an HTML file, with a filename built from a pk (optionally, some other field, such as a slug). 

The main code is in 'static_models.utils.ModelGenerator', which is well-documented. If you need a different kind of action, try look there.

## Install
The code can either be downloaded from Github, or installed using Pip,

    pip3 install django-static-models

The code needs to be declared in settings.py,

    INSTALLED_APPS = [
         'static_models.apps.StaticModelsConfig',
    ]


## Configuration
Is one of the most complex you will meet. Sorry, but the setup offers flexibility. A simple configuration is,

    STATIC_MODELVIEWS = [
        {
        'model' : 'page.Page', 
        'view' : 'page.views.PageDetailView',
        },
    ]
    ...

This will render the model Page through the view PageDetailView. It will search for all Page objects, push the data in to the generator, which will render the output webpages one-by-one. These will be written to files in a top-level directory called 'sites/page'. The trailing section of the path comes from the name of the model. The output files will be named by the 'pk' e.g. '3.html'. For further details and adjustments that can be made, see [Management commands](#management-commands).

Sometimes you will not want to use the 'pk' data to name the files. Configure like this,

    STATIC_MODELVIEWS = [
        {
        'model' : 'page.Page', 
        'view' : 'page.views.PageDetailView',
        'id_fieldname' : 'slug'
        },
    ]

'id_fieldname' says use the 'slug' field to name the files (this presumes the model Pages has a field called 'slug'). So now, in the 'sites' directory, the app may generate 'web-lunacy.html', not '3.html'.


Sometimes you will not want to use the model name to name the pathroot of the files. Configure like this,

    STATIC_MODELVIEWS = [
        {
        'model' : 'page.Page', 
        'view' : 'page.views.PageDetailView',
        'id_fieldname' : 'slug'
        'pathroot' : 'arrticle'
        },
    ]

Now the files go to 'site/article', not 'site/page'. You can substitute any path in 'pathroot', the filename is appended to the value.

A further trick. Django Model objects are designed to be general items, accessible through attributes. You can substitute your own dict data to imitate a set of Model objects, then push them into a view. This is naturally limited, you will not want to configure twenty objects like this. But it will allow you to generate a few special webpages, and also use views that do not accept models,


    STATIC_MODELVIEWS = [
        {
        'model' : [{'slug': 'about'}, {'slug':'terms'}, {'slug': 'contact'}], 
        'view' : 'mud.views.site_pages_view.BasePagesView',
        'id_fieldname' : 'slug'
        },
    ]

This assumes BasePagesView accepts a URL with a 'slug' placeholder. Note also that 'id_fieldname' continues to work in this setup, and so will name the generated files as the given 'slug' field e.g. 'about.html'.


## Management commands
The main way of invoking the configuration. Typically,

    ./manage.py modelstaticmerge

-  -o, --overwrite       Replace currently existing files (default is to ignore)
- -e, --html_extension  Add '.html' extension to generated files.


So,

    ./manage.py modelstaticmerge -e

Will generate HTML files from the configuration. From the second configuration above the files will be put in site/page/ and will be named from the slug data + '.html'.

By default modelstaticmerge will generate files where it finds no static file exists. And it will overwrite files that are not the same size as files it generates. It assumes these have been altered. But it will not modify files that are the same size.  This introduces some 'rclone' type behaviour. If you are using deployment or backup tools like 'rclone', they will be able to detect new and changed files themselves, and act efficiently. 

The management command is a little stripped down. You can do the same, with a few more options, by using the shell to import the ModelGenerator class from static_models.utils. 


## ModelGenerator
Offers options which may be of use.

    path_includes_view
        Path includes the view name. Default False

If a pathroot is not offered, the path is generated from the path and the view. From the above examples, you might generate 'site/page/page-detail-view/web-lunacy.html'. This is a little deep for me, but it namespaces by the view. So if you want to generate pages from a model using more than one view, you should use this, or explicitly override to different destinations using 'pathroot'.


## Viewing files
I suggest to start you go look at the generated file. Try loading to a browser, see what happens. Straight away you will see the issue.

The generated pages will have correct internal links ie. for resources like CSS or image links. But...

### Servers and browsers default files without extensions
This applies to Django development servers and to deployment servers like Apache and Nginx. 

If you used this app's default setup, you will generate files without an 'htm/html' extension. The files are named,

    site/page/many-wonders

Not,

    site/page/many-wonders.html

A browser or server will usually read these as an 'octet-stream', not a HTML file. They will not show the page, they will offer a download. 

This is an issue with static page serving, not this app or Django. There are ways round this.

#### Use the app facilities to generate extensions
That way, every page will load and display. The issue with this is that links between pages will be broken. And your project will loose any pretty URL setup. So, of course, you can rewrite your templates to add extensions to links. Or you may not care about dev viewing. Remember, these files are not what the dev server will be using for viewing, unless you [set up a URL]().


#### Coax the server into using a different default type
Browsers will not be able to read the files, they almost always use the extension, not the MIME type of the file. However, coaxing the server into seeing files as a different type is not as difficult as it sounds. It depends on your server. But if you can ask it to accept file types without an extension as MIME type 'text/html', you are up and running.

As for delivery, there are another option. Many deployment servers would allow you to rewrite the filename with an extension. Which is web-classic form, and guaranteed.
 

## Viewing files in development
Django static app has a middleware solution, where any URL looking for a file seeks first in the static' folder, and if that fails, goes hunting round the apps.

It would be interesting to have a parallel process for the static pages, but I've not implemented this. However, I have bashed together a View that can deliver the pages, even with no extension. Put this in ''urls.py',

    from django.conf import settings
    from static_models.views import StaticView
        ...
    path('site/<path:path>/', StaticView.as_view(path_root= settings.BASE_DIR  + '/site/'), name='site-detail'),

This code uses a setting BASE_DIR. StaticView has no opinion on the pathstyle. Now you can see all the static files on the URL 'site/...'. Such as 'site/page/many-wonders/'.

If there is a problem with the above, it is that links between pages will not work. All pages have been re-rooted to a URL root 'site'. A link like 'page/many-wonders' will now be broken. It needs to be 'site/page/many-wonders'. And we don't want to configure a URL for web root ('/') because likely you have some home page or other good use for that.
 
As a partial solution, StaticView also accepts 'pk' and 'slug' segment captures. So you can generate static pages, then rewrite urls.py, e.g. 

    from django.conf import settings
    from static_models.views import StaticView
        ...

    # New URL for static pages
    path('page/<slug:slug>/', StaticView.as_view(path_root= settings.MEDIA_ROOT + '/site/page/'), name='page-detail'),

    # original URL for dynamic pages
    #path('page/<slug:slug>/',  PageDetailView.as_view(), name='page-detail'), 

Now links between pages work. So reverse URLs. But you will need to set up a URL path for every model you generate static files from.


### Static definition, in the View, of path_root 
This is not something that would be of interest to many.

You can define path_root using a custom class declaration, With that you can configure fancy URL resolution/HTTP responses etc. e.g.

    from django.conf import settings
    from static_models.views import StaticView

    class PageStaticView(StaticView):
        path_root = settings.MEDIA_ROOT + '/site/page/'
        ...

And in ''urls.py',

    from page.views import PageStaticView
        ...
        path('page/<int:pk>/', PageStaticView.as_view(), name='page-detail'),


## Generating URL'/' root
If you are planning an complete static site, as opposed to boosting part of your site, you may run into the Djanog root abstraction. Django serves static files from the 'static/' directory, not the root. It has no analogy for a physical base 'root' directory. It either errors, or gets a configured URL. So what will you do with '/'?

Well, most visual websites will have a 'home' page of some kind. You could cook something up in deployment, and ignore anything that doesn't work through page generation. Or you could take advantage of this app's pseudo-model generation, and generate an 'index.html' page from your project's 'home' page view. That's the kind of purpose the pseudo-model code was added for.



## Maintaining a tree of static webpages
Run the management command whenever you update. Or automate the process in a deploy script. Another way is to run a maintenance command periodically. 

If you want to merge eagerly and automatically, there's a few ways, none are wonderful. I'd favour using the post_save signal in 'apps.py'. That will work with all model changes, and contains the logic within an app,

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

