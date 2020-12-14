# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

import debug_toolbar

urlpatterns = [
    # Debug toolbar
    path('__debug__/', include(debug_toolbar.urls)),
    # GCC
    path('', include('gcc.urls', namespace='gcc')),
    # GCC
    path('user/', include('users.urls', namespace='users')),
    # Oauth
    path(
        'user/auth/',
        include('proloauth_client.urls', namespace='proloauth_client'),
    ),
    # Django simple captcha
    path('captcha/', include('captcha.urls')),
    # Built-in Django admin
    path('admin/', admin.site.urls),
    # Language selector
    path('lang/', include('django.conf.urls.i18n')),
    # News (blog)
    path('news/', include('news.urls')),
    # Mass mailer
    path('mailing/', include('massmailer.urls')),
]

if settings.DEBUG:
    urlpatterns.extend(
        [
            path('e/400/', TemplateView.as_view(template_name='400.html')),
            path('e/403/', TemplateView.as_view(template_name='403.html')),
            path('e/404/', TemplateView.as_view(template_name='404.html')),
            path('e/500/', TemplateView.as_view(template_name='500.html')),
        ]
    )
