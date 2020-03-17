# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import random
from datetime import datetime

from django.conf import settings
from django.contrib import auth, messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView

from gcc.forms import (
    ApplicationWishesForm,
    CombinedApplicantUserForm,
    EmailForm,
)
from gcc.models import (
    Applicant,
    ApplicantStatusTypes,
    Edition,
    Event,
    EventWish,
    Sponsor,
    SubscriberEmail,
)
from prologin.email import send_email
from rules.contrib.views import PermissionRequiredMixin
from zinnia.models import Entry

# Editions


class EditionsView(TemplateView):
    template_name = "gcc/editions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['editions'] = Edition.get_all_editions()

        return context


# Privacy


class PrivacyView(TemplateView):
    template_name = "gcc/privacy.html"


# Homepage


class IndexView(FormView):
    template_name = "gcc/index.html"
    form_class = EmailForm
    success_url = reverse_lazy("gcc:index")

    def form_valid(self, form):
        instance, created = SubscriberEmail.objects.get_or_create(
            email=form.cleaned_data['email']
        )

        if created:
            messages.add_message(
                self.request, messages.SUCCESS, _('Subscription succeeded')
            )
            send_email(
                'gcc/mails/subscribe',
                instance.email,
                {'unsubscribe_url': instance.unsubscribe_url},
            )
        else:
            messages.add_message(
                self.request,
                messages.WARNING,
                _('Subscription failed: already subscribed'),
            )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        articles = Entry.published.prefetch_related('authors').all()[
            : settings.HOMEPAGE_ARTICLES
        ]
        context.update(
            {
                'last_edition': Edition.objects.latest(),
                'sponsors': list(Sponsor.objects.active()),
                'articles': articles,
            }
        )
        context['events'] = Event.objects.filter(
            signup_start__lt=timezone.now(),
            signup_end__gt=timezone.now(),
            edition=context['last_edition'],
        ).order_by('event_start')
        random.shuffle(context['sponsors'])
        return context


# Ressources, Learn More


class RessourcesView(TemplateView):
    template_name = "gcc/resources.html"


class LearnMoreView(TemplateView):
    template_name = "gcc/learn_more.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'last_edition': Edition.objects.latest(),
                'SITE_HOST': settings.SITE_HOST,
            }
        )
        context['events'] = Event.objects.filter(
            signup_start__lt=timezone.now(),
            signup_end__gt=timezone.now(),
            edition=context['last_edition'],
        ).order_by('event_start')
        return context


# Newsletter


class NewsletterUnsubscribeView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('gcc:index')

    def get(self, request, *args, **kwargs):
        try:
            subscriber = SubscriberEmail.objects.get(email=kwargs['email'])

            if subscriber.unsubscribe_token == kwargs['token']:
                subscriber.delete()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('Successfully unsubscribed from newsletter.'),
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _('Failed to unsubscribe: wrong token.'),
                )
        except SubscriberEmail.DoesNotExist:
            messages.add_message(
                request,
                messages.ERROR,
                _('Failed to unsubscribe: unregistered address'),
            )

        return super().get(request, *args, **kwargs)


# Application


class ApplicationSummaryView(PermissionRequiredMixin, DetailView):
    model = auth.get_user_model()
    context_object_name = 'shown_user'
    template_name = 'gcc/application/summary.html'
    permission_required = 'users.edit'
    success_url = reverse_lazy("gcc:summary")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = context[self.context_object_name]

        context.update(
            {
                'shown_user': shown_user,
                'current_edition': Edition.current(),
                'applicant': get_object_or_404(
                    Applicant, user=shown_user, edition=Edition.current()
                ),
                'has_applied_to_current': Edition.current().user_has_applied(
                    shown_user
                ),
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        result = super().get(request, *args, **kwargs)
        if not self.object.is_active and not self.request.user.is_staff:
            raise Http404()
        return result


class ApplicationValidationView(PermissionRequiredMixin, DetailView):
    model = auth.get_user_model()
    context_object_name = 'shown_user'
    template_name = 'gcc/application/validation.html'
    permission_required = 'users.edit'

    def get(self, request, *args, **kwargs):
        result = super().get(request, *args, **kwargs)
        if not self.object.is_active and not self.request.user.is_staff:
            raise Http404()
        return result

    # TODO: remove redondancy of get
    def get_context_data(self, **kwargs):
        applicant = get_object_or_404(
            Applicant, user=self.request.user, edition=self.kwargs['edition']
        )
        context = super().get_context_data(**kwargs)
        context['applicant'] = applicant
        return context

    def get_success_url(self):
        return reverse(
            'gcc:application_summary', kwargs={'pk': self.request.user.pk}
        )

    def post(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)

        applicant = get_object_or_404(
            Applicant, user=self.request.user, edition=kwargs['edition']
        )

        if not applicant.has_complete_application():
            messages.add_message(
                request,
                messages.ERROR,
                _(
                    'Failed to validate your application, your '
                    'profile is incomplete.'
                ),
            )
        else:
            applicant.validate_current_wishes()
            messages.add_message(
                request,
                messages.SUCCESS,
                _('Successfully validated your application.'),
            )

        if not self.object.is_active and not self.request.user.is_staff:
            raise Http404()

        return HttpResponseRedirect(
            reverse(
                'gcc:application_summary', kwargs={'pk': self.request.user.pk}
            )
        )


class ApplicationFormView(FormView):
    template_name = 'gcc/application/form.html'
    form_class = CombinedApplicantUserForm

    def dispatch(self, request, *args, **kwargs):
        # Redirect if already validated for this year.
        if request.user.is_anonymous:
            return super().dispatch(request, *args, **kwargs)

        edition = get_object_or_404(Edition, year=kwargs['edition'])
        applicant = Applicant.for_user_and_edition(self.request.user, edition)

        if applicant.is_locked():
            messages.add_message(
                request,
                messages.ERROR,
                _(
                    'Your application has already been validated, if you '
                    'really want to change something contact us by email.'
                ),
            )
            return HttpResponseRedirect(
                reverse(
                    'gcc:application_summary',
                    kwargs={'pk': self.request.user.pk},
                )
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['applicant'] = get_object_or_404(
            Applicant,
            edition__year=self.kwargs['edition'],
            user=self.request.user,
        )
        return context

    def get_object(self, queryset=None):
        # available from prologin.middleware.ContestMiddleware
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        kwargs['user'] = self.request.user
        kwargs['edition'] = get_object_or_404(
            Edition, year=self.kwargs['edition']
        )
        return kwargs

    def get_success_url(self):
        return reverse(
            'gcc:application_wishes',
            kwargs={
                'edition': get_object_or_404(
                    Edition, year=self.kwargs['edition']
                )
            },
        )

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ApplicationWishesView(FormView, PermissionRequiredMixin):
    template_name = 'gcc/application/wishes.html'
    form_class = ApplicationWishesForm
    permission_required = 'gcc.can_edit_own_application'

    def get_permission_object(self):
        return get_object_or_404(
            Applicant,
            user=self.request.user,
            edition__year=self.kwargs['edition'],
        )

    def get_success_url(self):
        return reverse(
            'gcc:application_summary', kwargs={'pk': self.request.user.pk}
        )

    def get_form_kwargs(self):
        # Specify the edition to the form's constructor
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                'edition': get_object_or_404(
                    Edition, year=self.kwargs['edition']
                ),
                'user': self.request.user,
            }
        )
        return kwargs

    def get_initial(self):
        event_wishes = EventWish.objects.filter(
            applicant__user=self.request.user,
            applicant__edition__year=self.kwargs['edition'],
        )
        initials = {}

        for wish in event_wishes:
            assert wish.order in [1, 2, 3]
            field_name = 'priority' + str(wish.order)
            initials[field_name] = wish.event.pk

        return initials

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.filter(
            signup_start__lt=timezone.now(),
            signup_end__gt=timezone.now(),
            edition=self.kwargs['edition'],
        ).order_by('event_start')
        return context

    def form_valid(self, form):
        edition = get_object_or_404(Edition, year=self.kwargs['edition'])
        form.save(self.request.user, edition)
        return super().form_valid(form)


class ApplicationConfirmVenueView(PermissionRequiredMixin, RedirectView):
    permission_required = 'users.edit'

    def get_permission_object(self):
        return get_object_or_404(
            EventWish, pk=self.kwargs['wish']
        ).applicant.user

    def get_redirect_url(self, *args, **kwargs):
        wish = get_object_or_404(EventWish, pk=kwargs['wish'])
        return reverse(
            'gcc:application_summary', kwargs={'pk': wish.applicant.user.pk}
        )

    def get(self, request, *args, **kwargs):
        if self.has_permission():
            wish = get_object_or_404(EventWish, pk=kwargs['wish'])

            if wish.status == ApplicantStatusTypes.accepted.value:
                wish.status = ApplicantStatusTypes.confirmed.value
                wish.save()
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    _('Confirmation completed, thank you for your help!'),
                )

        return super().get(request, *args, **kwargs)
