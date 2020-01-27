# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.urls import path, include
from users import views

app_name = 'users'

user_patterns = [
    path('profile', views.ProfileView.as_view(), name='profile'),
    path('edit', views.EditUserView.as_view(), name='edit'),
]

urlpatterns = [
    # User profile, view and edit
    path('<int:pk>/', include(user_patterns)),
    # Logout (login is fuly handled by oauth)
    path('logout', views.LogoutView.as_view(), name='logout'),
    # Mailing unsubscribe
    path('unsubscribe', views.UnsubscribeView.as_view(), name='unsubscribe'),
]
