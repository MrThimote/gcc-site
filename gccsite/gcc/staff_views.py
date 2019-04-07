from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, TemplateView
from rules.contrib.views import PermissionRequiredMixin

from gcc.models import (Applicant, ApplicantLabel, ApplicantStatusTypes, Event,
                        EventWish)


class ApplicationReviewIndexView(PermissionRequiredMixin, TemplateView):
    permission_required = 'gcc.can_review'
    template_name = "gcc/application/review_index.html"

    def get_context_data(self, **kwargs):
        """
        Extract the list of users who have an application this year and list
        their applications in the same object.
        """
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.all().prefetch_related(
            'center', 'edition').order_by('edition')
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
            'user', 'answers', 'answers__question', 'eventwish_set',
            'eventwish_set__event', 'labels')

        #TODO: remove redundancy
        assert event.edition.year == kwargs['edition']

        context = super().get_context_data(**kwargs)
        context.update({
            'applicants': applicants,
            'event': event,
            'labels': ApplicantLabel.objects.all()
        })
        return context


class ApplicationRemoveLabelView(PermissionRequiredMixin, View):
    permission_required = 'gcc.can_edit_application_labels'

    def get_permission_object(self):
        return get_object_or_404(Applicant, pk=self.kwargs['applicant'])

    def get(self, request, *args, **kwargs):
        try:
            applicant = Applicant.objects.get(pk=kwargs['applicant'])
            label = ApplicantLabel.objects.get(pk=kwargs['label'])
        except Applicant.DoesNotExist:
            return JsonResponse({'status': 'error',
                                 'reason': _('applicant does not exist')})
        except ApplicantLabel.DoesNotExist:
            return JsonResponse({'status': 'error',
                                 'reason': _('label does not exist')})

        if not self.has_permission():
            return JsonResponse({'status': 'error',
                                 'reason': _('not allowed')})

        if label not in applicant.labels.all():
            return JsonResponse({'status': 'error',
                                 'reason': 'label not applied'})

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
            return JsonResponse({'status': 'error',
                                 'reason': _('applicant does not exist')})
        except ApplicantLabel.DoesNotExist:
            return JsonResponse({'status': 'error',
                                 'reason': _('label does not exist')})

        if not self.has_permission():
            return JsonResponse({'status': 'error',
                                 'reason': _('not allowed')})

        if label in applicant.labels.all():
            return JsonResponse({'status': 'error',
                                 'reason': 'label already applied'})

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
            return JsonResponse({'status': 'error',
                                 'reason': _('wish does not exist')})

        if not self.has_permission():
            return JsonResponse({'status': 'error',
                                 'reason': _('not allowed')})

        if wish.status == status:
            return JsonResponse({'status': 'error',
                                 'reason': 'wish already accepted'})

        wish.status = status
        wish.save()
        return JsonResponse({
            'status': 'ok',
            'applicant': wish.applicant.pk,
            'applicant-status': wish.applicant.get_status_display()})
