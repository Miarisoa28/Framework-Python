"""
URL configuration for gpi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

# project/urls.py (remplacer 'project' par le nom de ton projet Django)
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
#from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('messagerie/', include('messagerie.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', lambda request: redirect('liste_conversations'), name='base'),
    #path('nouvelle_conversation/<int:utilisateur_id>/', views.nouvelle_conversation, name='nouvelle_conversation'),
    #path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
]
