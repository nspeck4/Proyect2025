from tkinter.font import names

from django.conf.urls.i18n import urlpatterns
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
]