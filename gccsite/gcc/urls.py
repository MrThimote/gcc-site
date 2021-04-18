# Copyright (C) <2018> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import include, path

from gcc import staff_views, views

app_name = 'gcc'


def crash_test(request):
    if request.user.is_authenticated:
        1 / 0
    return HttpResponse(status=204)


NEWSLETTER_PATTERNS = [
    path(
        'unsubscribe/<str:email>/<str:token>/',
        views.NewsletterUnsubscribeView.as_view(),
        name='news_unsubscribe',
    ),
    path(
        'subscribe/<str:email>/<str:token>/',
        views.NewsletterVerifySubscribeView.as_view(),
        name='news_verify',
    )
]

APPLICATION_PATTERNS = [
    path(
        'review/',
        staff_views.ApplicationReviewIndexView.as_view(),
        name='application_review_index',
    ),
    path(
        'review/<int:edition>/<int:event>/',
        staff_views.ApplicationReviewView.as_view(),
        name='application_review',
    ),
    path(
        'validation/<int:pk>/<int:edition>/',
        views.ApplicationValidationView.as_view(),
        name='application_validation',
    ),
    path(
        'form/<int:edition>/',
        login_required(
            views.ApplicationFormView.as_view(),
            login_url='https://prologin.org/user/login',
        ),
        name='application_form',
    ),
    path(
        'wishes/<int:edition>/',
        views.ApplicationWishesView.as_view(),
        name='application_wishes',
    ),
    path(
        'summary/<int:pk>/',
        views.ApplicationSummaryView.as_view(),
        name='application_summary',
    ),
    path(
        'confirm/<int:wish>/',
        views.ApplicationConfirmVenueView.as_view(),
        name='confirm',
    ),
    path(
        'label_remove/<int:event>/<int:applicant>/<int:label>/',
        staff_views.ApplicationRemoveLabelView.as_view(),
        name='delete_applicant_label',
    ),
    path(
        'label_add/<int:event>/<int:applicant>/<int:label>/',
        staff_views.ApplicationAddLabelView.as_view(),
        name='add_applicant_label',
    ),
    path(
        'update_wish/<int:wish>/<int:status>/',
        staff_views.UpdateWish.as_view(),
        name='update_wish',
    ),
    path(
        'accept_all/<int:event>/',
        staff_views.ApplicationAcceptView.as_view(),
        name='accept_all',
    ),
    path(
        'accept_all_send/<int:event>/',
        staff_views.ApplicationAcceptSendView.as_view(),
        name='accept_all_send',
    ),
]

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('crashtest/', crash_test),
    path('application/', include(APPLICATION_PATTERNS)),
    path('newsletter/', include(NEWSLETTER_PATTERNS)),
    path('learn/', views.LearnMoreView.as_view(), name='learn_more'),
    path('resources/', views.RessourcesView.as_view(), name='resources'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('editions/', views.EditionsView.as_view(), name='editions'),
    path(
        'editions/<int:year>/', views.EditionsView.as_view(), name='editions'
    ),
    path('tutorials/', views.TutorialsView.as_view(), name='tutorials'),
    # Remove after february 2020: candidates received a wrong url
    path(
        'confirm/<int:wish>/',
        views.ApplicationConfirmVenueView.as_view(),
        name='confirm',
    ),
    # Admin panel
    path('admin/', admin.site.urls),
]
