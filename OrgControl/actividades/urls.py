from django.urls import path, include
from .views import (
    PlanAnualCreateView,
    ActividadCreateView,
    PlanAnualDetailView,
    PlanAnualListView
)




urlpatterns = [
    path('planes/', PlanAnualListView.as_view(), name='plan_anual_list'),
    path('planes/nuevo/', PlanAnualCreateView.as_view(), name='plan_anual_create'),
    path('planes/<int:pk>/', PlanAnualDetailView.as_view(), name='plan_anual_detail'),
    path('planes/<int:plan_id>/actividad/nueva/', ActividadCreateView.as_view(), name='actividad_create'),
]