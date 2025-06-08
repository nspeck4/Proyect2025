from django.urls import path
from . import views
from .views import UserListView, UserUpdateView, UserDeleteView
from .views import profile_view, profile_edit

app_name = 'users'

urlpatterns = [
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/new/', views.create_user, name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),

    path('organization/', views.organization_structure, name='organization_structure'),
    path('organization/new/', views.create_organization_level, name='organization_level_create'),

    path('approval-flows/', views.approval_flows, name='approval_flows'),
    path('approval-flows/<int:flow_id>/approvers/', views.manage_approvers, name='manage_approvers'),
# ... otras URLs
    path('profile/', profile_view, name='profile_view'),
    path('profile/edit/', profile_edit, name='profile_edit'),
]