# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

"""
Django common settings for GCC project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from collections import namedtuple
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

SITE_ID = 1

# Application definition

INSTALLED_APPS = (
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Vendor
    'adminsortable',
    'bootstrap3',
    'bootstrapform',
    'compat',
    'crispy_forms',
    'django_bootstrap_breadcrumbs',
    'django_comments',
    'djmail',
    'proloauth_client',
    'rules.apps.AutodiscoverRulesConfig',
    'statictemplate',
    'tagging',
    # GCC apps
    'gccsite',
    'centers',
    'users',
    'gcc',
    'news',
    # Django and vendor, at the bottom for template overriding
    'django.contrib.admin',
    'zinnia',
    'massmailer',
    # Debug Toolbar (will not load if DEBUG = False)
    'debug_toolbar',
)

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'proloauth_client.middleware.RefreshTokenMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }
]

ROOT_URLCONF = 'gccsite.urls'

WSGI_APPLICATION = 'gccsite.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'fr'

LANGUAGES = (('en', _("English")), ('fr', _("French")))

TIME_ZONE = 'Europe/Paris'

LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

USE_I18N = True

USE_L10N = True

FORMAT_MODULE_PATH = ['formats']

USE_TZ = True

# Emails

DJMAIL_BODY_TEMPLATE_PROTOTYPE = "{name}.body.{type}.{ext}"
DJMAIL_SUBJECT_TEMPLATE_PROTOTYPE = "{name}.subject.{ext}"
DJMAIL_REAL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_BACKEND = "djmail.backends.default.EmailBackend"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR)

MEDIA_ROOT = os.path.join(PROJECT_ROOT_DIR, 'public', 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(PROJECT_ROOT_DIR, 'public', 'static')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'gcc.staticfinder.ArchivesStaticFinder',
    'npm.finders.NpmFinder',
)

SESSION_COOKIE_NAME = 'sessionid_gcc'

# Authentication

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'rules.permissions.ObjectPermissionBackend',
)
AUTH_USER_MODEL = 'users.GCCUser'

LOGIN_URL = reverse_lazy('proloauth_client:autologin')
LOGOUT_URL = reverse_lazy('users:logout')
LOGIN_REDIRECT_URL = reverse_lazy('gcc:index')

# Prologin specific
SITE_HOST = 'gcc.prologin.org'
SITE_BASE_URL = 'https://{}'.format(SITE_HOST)
PROLOGIN_CONTACT_MAIL = 'info@prologin.org'
DEFAULT_FROM_EMAIL = 'Prologin <{}>'.format(PROLOGIN_CONTACT_MAIL)
GOOGLE_ANALYTICS_ID = ''

ARCHIVES_REPOSITORY_PATH = os.path.join(PROJECT_ROOT_DIR, '..', 'archives')
ARCHIVES_REPOSITORY_STATIC_PREFIX = 'archives'

OAUTH_ENDPOINT = 'https://prologin.org/user/auth'
OAUTH_CLIENT_ID = 'gcc'

# Cache durations and keys
CacheSetting = namedtuple('CacheSetting', 'key duration')


# Debug toolbar


def show_toolbar_cb(req):
    from debug_toolbar.middleware import show_toolbar

    if not show_toolbar(req):
        return False
    # Disable for statictemplate
    if req.META['SERVER_NAME'] == 'testserver':
        return False
    return True


DEBUG_TOOLBAR_CONFIG = {
    # Already served
    'JQUERY_URL': '',
    'DISABLE_PANELS': {
        'debug_toolbar.panels.redirects.RedirectsPanel',
        # StaticFilesPanel takes *way* too much compute power
        # while being useless
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    },
    'SHOW_COLLAPSED': True,
    'SHOW_TOOLBAR_CALLBACK': show_toolbar_cb,
}

# Bootstrap configuration
BOOTSTRAP3 = {'success_css_class': ''}
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# NPM (static assets)
NPM_ROOT_PATH = os.path.join(PROJECT_ROOT_DIR, 'assets')
NPM_STATIC_FILES_PREFIX = 'vendor'
NPM_FILE_PATTERNS = {
    'bootstrap': ['dist/css/*.css', 'dist/js/*.js'],
    'font-awesome': ['css/*.css', 'fonts/*'],
    'jquery': ['dist/*.js'],
}

# ZINNIA (newsblog)

HOMEPAGE_ARTICLES = 4
ZINNIA_AUTO_CLOSE_COMMENTS_AFTER = 0  # disable comments
ZINNIA_AUTO_CLOSE_PINGBACKS_AFTER = 0  # disables pingbacks completely
ZINNIA_AUTO_CLOSE_TRACKBACKS_AFTER = 0  # disables trackbacks completely
ZINNIA_ENTRY_BASE_MODEL = 'news.models.NewsEntry'
ZINNIA_FEEDS_FORMAT = 'atom'
ZINNIA_FEEDS_MAX_ITEMS = 20
ZINNIA_MAIL_COMMENT_AUTHORS = False
ZINNIA_MARKUP_LANGUAGE = 'markdown'
ZINNIA_PING_DIRECTORIES = ()
ZINNIA_PING_EXTERNAL_URLS = False
ZINNIA_PROTOCOL = 'https'
ZINNIA_SAVE_PING_DIRECTORIES = False
ZINNIA_UPLOAD_TO = 'upload/zinnia'
