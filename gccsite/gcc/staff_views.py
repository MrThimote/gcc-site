# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import sys
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView, View
from prologin.email import send_email
from django.utils.text import slugify


from gcc.models import (
    Answer,
    Applicant,
    ApplicantLabel,
    ApplicantStatusTypes,
    Event,
    EventWish,
)
from rules.contrib.views import PermissionRequiredMixin


class ApplicationReviewIndexView(PermissionRequiredMixin, TemplateView):
    permission_required = 'gcc.can_review'
    template_name = "gcc/application/review_index.html"

    def get_context_data(self, **kwargs):
        """
        Extract the list of users who have an application this year and list
        their applications in the same object.
        """
        context = super().get_context_data(**kwargs)
        context['events'] = (
            Event.objects.all()
            .prefetch_related('center', 'edition')
            .order_by('edition', 'event_start')
        )
        return context


class ApplicationReviewView(PermissionRequiredMixin, TemplateView):
    permission_required = 'gcc.can_review_event'
    template_name = "gcc/application/review.html"

    def get_permission_object(self):
        return get_object_or_404(Event, pk=self.kwargs['event'])

    def get_context_data(self, **kwargs):
        """
        Extract the list of users who have an application this year and list
        their applications in the same object.
        """
        event = get_object_or_404(Event, pk=kwargs['event'])
        applicants = Applicant.objects.filter(assignation_wishes=event)
        applicants = applicants.prefetch_related(
            'user',
            'answers',
            'answers__question',
            'eventwish_set',
            'eventwish_set__event',
            'labels',
        )
        acceptable_applicants = Applicant.acceptable_applicants_for(event)

        # Group applicants by choice order
        grouped_applicants = dict()

        for applicant in applicants:
            order = EventWish.objects.get(
                applicant=applicant, event=event
            ).order

            if order not in grouped_applicants:
                grouped_applicants[order] = []

            grouped_applicants[order].append(applicant)

        for group in grouped_applicants.values():
            group.sort(
                key=lambda applicant: (
                    applicant.user.last_name.upper(),
                    applicant.user.first_name.upper(),
                )
            )

        grouped_applicants = sorted(grouped_applicants.items())

        # TODO: remove redundancy
        if event.edition.year != kwargs['edition']:
            raise Http404("Incorrect edition")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                'grouped_applicants': grouped_applicants,
                'event': event,
                'labels': ApplicantLabel.objects.all(),
                'nb_acceptables': len(acceptable_applicants),
            }
        )

        context['nb_accepted'] = len(Applicant.accepted_applicants_for(event))
        context['nb_confirmed'] = len(
            Applicant.confirmed_applicants_for(event)
        )
        context['nb_applicants'] = applicants.count()

        return context


#      _                      _        _   _
#     / \   ___ ___ ___ _ __ | |_ __ _| |_(_) ___  _ __  ___
#    / _ \ / __/ __/ _ \ '_ \| __/ _` | __| |/ _ \| '_ \/ __|
#   / ___ \ (_| (_|  __/ |_) | || (_| | |_| | (_) | | | \__ \
#  /_/   \_\___\___\___| .__/ \__\__,_|\__|_|\___/|_| |_|___/
#                      |_|


class ApplicationAcceptView(PermissionRequiredMixin, TemplateView):
    permission_required = 'gcc.can_review_event'
    template_name = 'gcc/application/accept.html'

    def get_permission_object(self):
        return get_object_or_404(Event, pk=self.kwargs['event'])

    def get_context_data(self, **kwargs):
        event = get_object_or_404(Event, pk=kwargs['event'])
        applicants = Applicant.acceptable_applicants_for(event)

        context = super().get_context_data(**kwargs)
        context.update({'applicants': applicants, 'event': event})
        return context


class ApplicationAcceptSendView(PermissionRequiredMixin, RedirectView):
    permission_required = 'gcc.can_review_event'

    def get_redirect_url(self, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs['event'])
        return reverse(
            'gcc:application_review',
            kwargs={'edition': event.edition, 'event': event.pk},
        )

    def get_permission_object(self):
        return get_object_or_404(Event, pk=self.kwargs['event'])

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs['event'])
        acceptables = Applicant.acceptable_applicants_for(event)

        for applicant in acceptables:
            wish = get_object_or_404(
                EventWish, applicant=applicant, event=event
            )

            try:
                #  def catch_attachment(path):
                #      return open(staticfiles_storage.path(path), 'rb').read()
                #
                #  event_center = str(event.center)
                #  event_date = event.event_start.strftime('%Y-%m-%d')
                #
                #  event_name = slugify(event_center + '-' + event_date)
                #
                #  attachments = (
                #      (
                #          'autorisation-participation.pdf',
                #          catch_attachment(
                #              'gcc/attachments/autorisation-participation-'
                #              + event_name
                #              + '.pdf'
                #          ),
                #          'application/pdf',
                #      ),
                #      (
                #          'planning.pdf',
                #          catch_attachment(
                #              'gcc/attachments/planning-' + event_name + '.pdf'
                #          ),
                #          'application/pdf',
                #      ),
                #      (
                #          'droits-image.pdf',
                #          catch_attachment(
                #              'gcc/attachments/droits-image-'
                #              + event_name
                #              + '.pdf'
                #          ),
                #          'application/pdf',
                #      ),
                #      (
                #          'fiche-sanitaire.pdf',
                #          catch_attachment(
                #              'gcc/attachments/fiche-sanitaire-'
                #              + event_name
                #              + '.pdf'
                #          ),
                #          'application/pdf',
                #      ),
                #  )
                #
                #  # TODO: CRITICAL: this is hardcoded pk of parent's email
                #  parent_email = Answer.objects.get(
                #      applicant=applicant, question__pk=17
                #  ).response
                #
                #  for dest in [applicant.user.email, parent_email]:
                #      confirm_url = (
                #          'https://'
                #          + settings.SITE_HOST
                #          + reverse('gcc:confirm', kwargs={'wish': wish.pk})
                #      )
                #
                #      send_email(
                #          'gcc/mails/accept',
                #          dest,
                #          {
                #              'applicant': applicant,
                #              'event': event,
                #              'confirm_url': confirm_url,
                #          },
                #          attachments,
                #      )

                wish.status = ApplicantStatusTypes.accepted.value
                wish.save()
            except Exception as exp:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    'Failed to accept: {}: {} ({}:{})'.format(
                        applicant.user.username, exp, fname, exc_tb.tb_lineno
                    ),
                )

        return super().get(request, *args, **kwargs)


#  __        ___     _                  ___     _          _          _
#  \ \      / (_)___| |__   ___  ___   ( _ )   | |    __ _| |__   ___| |___
#   \ \ /\ / /| / __| '_ \ / _ \/ __|  / _ \/\ | |   / _` | '_ \ / _ \ / __|
#    \ V  V / | \__ \ | | |  __/\__ \ | (_>  < | |__| (_| | |_) |  __/ \__ \
#     \_/\_/  |_|___/_| |_|\___||___/  \___/\/ |_____\__,_|_.__/ \___|_|___/

# Following views provide a Rest API to interact with status and labels of the
# candidates.


class ApplicationRemoveLabelView(PermissionRequiredMixin, View):
    permission_required = 'gcc.can_edit_application_labels'

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get(self, request, *args, **kwargs):
        try:
            applicant = Applicant.objects.get(pk=kwargs['applicant'])
            label = ApplicantLabel.objects.get(pk=kwargs['label'])
        except Applicant.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'reason': _('applicant does not exist')}
            )
        except ApplicantLabel.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'reason': _('label does not exist')}
            )

        if not self.has_permission():
            return JsonResponse(
                {'status': 'error', 'reason': _('not allowed')}
            )

        if label not in applicant.labels.all():
            return JsonResponse(
                {'status': 'error', 'reason': 'label not applied'}
            )

        applicant.labels.remove(label)
        return JsonResponse({'status': 'ok'})


class ApplicationAddLabelView(PermissionRequiredMixin, View):
    permission_required = 'gcc.can_edit_application_labels'

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get(self, request, *args, **kwargs):
        try:
            applicant = Applicant.objects.get(pk=kwargs['applicant'])
            label = ApplicantLabel.objects.get(pk=kwargs['label'])
        except Applicant.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'reason': _('applicant does not exist')}
            )
        except ApplicantLabel.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'reason': _('label does not exist')}
            )

        if not self.has_permission():
            return JsonResponse(
                {'status': 'error', 'reason': _('not allowed')}
            )

        if label in applicant.labels.all():
            return JsonResponse(
                {'status': 'error', 'reason': 'label already applied'}
            )

        applicant.labels.add(label)
        return JsonResponse({'status': 'ok'})


class UpdateWish(PermissionRequiredMixin, View):
    permission_required = 'gcc.can_accept_wish'

    def get_permission_object(self):
        return get_object_or_404(EventWish, pk=self.kwargs['wish'])

    def get(self, request, *args, **kwargs):
        try:
            wish = EventWish.objects.get(pk=kwargs['wish'])
            status = kwargs['status']
        except EventWish.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'reason': _('wish does not exist')}
            )

        if not self.has_permission():
            return JsonResponse(
                {'status': 'error', 'reason': _('not allowed')}
            )

        if wish.status == status:
            return JsonResponse(
                {'status': 'error', 'reason': 'wish already accepted'}
            )
        wish.status = status
        wish.save()

        nb_acceptables = len(Applicant.acceptable_applicants_for(wish.event))
        return JsonResponse(
            {
                'status': 'ok',
                'applicant': wish.applicant.pk,
                'applicant-status': wish.applicant.get_status_display(),
                'nb_acceptable_applicants': nb_acceptables,
            }
        )
