"""MOD-01 Authentication URLs — v3"""
from django.urls import path
from apps.authentication.views import (
    SecureLoginView, SecureLogoutView, ThrottledRefreshView,
    RegisterView, UserListView, UserDetailView, ProfileView,
    ChangePasswordView, RoleListView, AnalystListView, UnlockUserView
)

urlpatterns = [
    path('login/',                    SecureLoginView.as_view(),       name='login'),
    path('refresh/',                  ThrottledRefreshView.as_view(),  name='token_refresh'),
    path('logout/',                   SecureLogoutView.as_view(),      name='logout'),
    path('register/',                 RegisterView.as_view(),          name='register'),
    path('profile/',                  ProfileView.as_view(),           name='profile'),
    path('change-password/',          ChangePasswordView.as_view(),    name='change_password'),
    path('users/',                    UserListView.as_view(),          name='user_list'),
    path('users/<int:user_id>/',      UserDetailView.as_view(),        name='user_detail'),
    path('users/<int:user_id>/unlock/', UnlockUserView.as_view(),      name='user_unlock'),
    path('roles/',                    RoleListView.as_view(),          name='role_list'),
    path('analysts/',                 AnalystListView.as_view(),       name='analyst_list'),
]
