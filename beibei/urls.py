"""beibei URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import path

from api import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    url(r'^api/img/$', views.img),
    url(r'^api/user/login/$', views.login),
    url(r'^api/user/res/$', views.res),
    url(r'^api/word/upload/$', views.upload),
    url(r'^api/user/ref/$', views.ref),
    url(r'^api/study/$', views.study),
    url(r'^api/word/(?P<id>\d+)/$', views.word),
    url(r'^api/user/setting/$', views.setting),
    url(r'^api/user/$', views.user),
    url(r'^api/user/study/$', views.userStudy),
    url(r'^api/word/del/(?P<id>\d+)/$', views.delWord),
    path('api/word/all/', views.WordView.as_view()),
    url(r'^api/word/$', views.getWord),
    url(r'^api/study/ok/$', views.ok),
    url(r'^api/user/pw/$', views.pw),
]
