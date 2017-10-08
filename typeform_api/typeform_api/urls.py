from django.conf.urls import url, include
from django.contrib import admin
from api.api_views import *
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    #API URLS
    url(r'^typeapi/add/', add_new),
]
