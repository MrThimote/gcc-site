# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import hashlib
import os
from collections import OrderedDict
from datetime import date

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.formats import date_format
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_noop

from adminsortable.models import SortableMixin
from centers.models import Center
from prologin.models import AddressableModel, ContactModel, EnumField
from prologin.utils import ChoiceEnum, upload_path


class Edition(models.Model):
    year = models.PositiveIntegerField(primary_key=True, unique=True)
    signup_form = models.ForeignKey('Form', on_delete=models.CASCADE)
    long_description = models.TextField(default="")

    @cached_property
    def poster_url(self):
        """Gets poster's URL if it exists else return None"""
        name = 'poster.full.jpg'
        path = os.path.abspath(
            os.path.join(
                settings.ARCHIVES_REPOSITORY_PATH, 'gcc', str(self.year), name,
            )
        )

        if not os.path.exists(path):
            return None

        return self.file_url(name)

    def file_path(self, *tail):
        """Gets file's absolute path"""
        return os.path.abspath(
            os.path.join(settings.GCC_REPOSITORY_PATH, str(self.year), *tail)
        )

    def file_url(self, *tail):
        """Gets file's URL"""
        return os.path.join(
            settings.STATIC_URL,
            settings.GCC_REPOSITORY_STATIC_PREFIX,
            str(self.year),
            *tail,
        )

    @staticmethod
    def current():
        """Gets current edition"""
        return Edition.objects.filter(year=int(settings.GCC_EDITION))

    def subscription_is_open(self):
        """Is there still one event open for subscription"""
        current_events = Event.objects.filter(
            edition=self,
            signup_start__lt=timezone.now(),
            signup_end__gte=timezone.now(),
        )
        return current_events.exists()

    def user_has_applied(self, user):
        """Check whether a user has applied for this edition"""
        return Applicant.objects.filter(user=user, edition=self).exists()

    @staticmethod
    def get_all_editions():
        return Edition.objects.all()

    def get_all_images(self):
        path = os.path.abspath(
            os.path.join(
                settings.ARCHIVES_REPOSITORY_PATH,
                'gcc',
                str(self.year),
                'photos',
            )
        )

        url = self.file_url('photos')

        return [
            os.path.join(url, name)
            for name in os.listdir(path)
            if os.path.isfile(os.path.join(path, name))
        ]

    def __str__(self):
        return str(self.year)

    class Meta:
        ordering = ['-year']
        get_latest_by = ['year']


class Event(models.Model):
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)
    is_long = models.BooleanField(default=True)
    event_start = models.DateTimeField()
    event_end = models.DateTimeField()
    signup_start = models.DateTimeField()
    signup_end = models.DateTimeField()
    signup_form = models.ForeignKey(
        'Form', on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return (
            self.event_start.strftime('%Y-%m-%d')
            + ' - '
            + self.event_start.strftime('%Y-%m-%d')
            + ' '
            + str(self.center)
        )

    def csv_name(self):
        return (
            self.event_start.strftime('%Y-%m-%d')
            + '_'
            + str(self.center).replace(' ', '_')
        )

    def short_description(self):
        return '{name} – {start} to {end}'.format(
            name=self.center.name,
            start=date_format(self.event_start, "SHORT_DATE_FORMAT"),
            end=date_format(self.event_end, "SHORT_DATE_FORMAT"),
        )


class Corrector(models.Model):
    event = models.ForeignKey(
        'Event', on_delete=models.CASCADE, related_name='correctors'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.user)


class ApplicantLabel(models.Model):
    """Labels to comment on an applicant"""

    display = models.CharField(max_length=10)

    def __str__(self):
        return self.display


@ChoiceEnum.labels(str.capitalize)
class ApplicantStatusTypes(ChoiceEnum):
    incomplete = 0  # the candidate hasn't finished her registration yet
    pending = 1  # the candidate finished her registration
    rejected = 2  # the candidate's application has been rejected
    selected = 3  # the candidate has been selected for participation
    accepted = 4  # the candidate has been assigned to an event and emailed
    confirmed = 5  # the candidate confirmed her participation


# Increasing order of status, for example, if the wishes of a candidate have
# separate status, the greatest one is displayed
STATUS_ORDER = [
    ApplicantStatusTypes.rejected.value,
    ApplicantStatusTypes.incomplete.value,
    ApplicantStatusTypes.pending.value,
    ApplicantStatusTypes.selected.value,
    ApplicantStatusTypes.accepted.value,
    ApplicantStatusTypes.confirmed.value,
]


class Applicant(models.Model):
    """
    An applicant for a specific edition and reviews about him.

    Notice that no free writing field has been added yet in order to ensure an
    GDPR-safe usage of reviews.
    """

    # General informations about the application
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)

    # Wishes of the candidate
    # TODO: Rename as assignation_event is deprecated
    assignation_wishes = models.ManyToManyField(
        Event, through='EventWish', related_name='applicants', blank=True
    )

    # Wishes she is accepted to
    # TODO: Deprecated (use wish-specific status)
    assignation_event = models.ManyToManyField(
        Event, related_name='assigned_applicants', blank=True
    )

    # Review of the application
    labels = models.ManyToManyField(ApplicantLabel, blank=True)

    @property
    def status(self):
        wishes_status = set(wish.status for wish in self.eventwish_set.all())

        for wish_status in reversed(STATUS_ORDER):
            if wish_status in wishes_status:
                return wish_status

        return ApplicantStatusTypes.incomplete.value

    def is_locked(self):
        return EventWish.objects.filter(
            ~Q(
                status__in=[
                    ApplicantStatusTypes.incomplete.value,
                    ApplicantStatusTypes.rejected.value,
                ]
            ),
            applicant=self,
        ).exists()

    def has_rejected_choices(self):
        return EventWish.objects.filter(
            applicant=self, status=ApplicantStatusTypes.rejected.value
        ).exists()

    def has_non_rejected_choices(self):
        return EventWish.objects.filter(
            ~Q(status=ApplicantStatusTypes.rejected.value), applicant=self
        ).exists()

    def get_export_data(self):
        """
        Return an array of data to be converted to csv
        """

        export_datas = OrderedDict()
        export_datas["Username"] = self.user.username
        export_datas["First name"] = self.user.first_name
        export_datas["Last name"] = self.user.last_name
        export_datas["Email"] = self.user.email
        export_datas["Edition"] = str(self.edition)
        export_datas["Labels"] = str(self.labels)

        questions = self.edition.signup_form.question_list.all()

        for question in questions:
            try:
                answer = Answer.objects.get(applicant=self, question=question)
                export_datas[str(question)] = str(answer)
            except Answer.DoesNotExist:
                export_datas[str(question)] = "(empty)"

        return export_datas

    def get_status_display(self):
        return ApplicantStatusTypes(self.status).name

    def list_of_assignation_wishes(self):
        return [event for event in self.assignation_wishes.all()]

    def list_of_assignation_event(self):
        return [event for event in self.assignation_event.all()]

    def has_complete_application(self):
        # TODO: optimize requests
        if not self.user.has_complete_profile():
            return False

        questions = Edition.current().signup_form.question_list.all()
        for question in questions:
            try:
                answer = Answer.objects.get(applicant=self, question=question)
                if not answer.is_valid():
                    return False
            except Answer.DoesNotExist:
                return question.finaly_required

        return True

    def validate_current_wishes(self):
        for wish in self.eventwish_set.all():
            if wish.status == ApplicantStatusTypes.incomplete.value:
                wish.status = ApplicantStatusTypes.pending.value
                wish.save()

    @staticmethod
    def incomplete_applicants_for(event):
        """
        List the applicants which are incomplete.
        """
        acceptable_wishes = EventWish.objects.filter(
            event=event, status=ApplicantStatusTypes.incomplete.value
        )
        return [wish.applicant for wish in acceptable_wishes]

    @staticmethod
    def acceptable_applicants_for(event):
        """
        List the applicants which are waiting to be accepted (ie. in the state
        `selected`).
        """
        acceptable_wishes = EventWish.objects.filter(
            event=event, status=ApplicantStatusTypes.selected.value
        )
        return [wish.applicant for wish in acceptable_wishes]

    @staticmethod
    def accepted_applicants_for(event):
        """
        List the applicants which are accepted but did not confirm.
        """
        accepted_wishes = EventWish.objects.filter(
            event=event, status=ApplicantStatusTypes.accepted.value
        )
        return [wish.applicant for wish in accepted_wishes]

    @staticmethod
    def confirmed_applicants_for(event):
        """
        List the applicants which are confirmed.
        """
        confirmed_wishes = EventWish.objects.filter(
            event=event, status=ApplicantStatusTypes.confirmed.value
        )
        return [wish.applicant for wish in confirmed_wishes]

    @staticmethod
    def rejected_applicants_for(event):
        """
        List the applicants which were rejected.
        """
        acceptable_wishes = EventWish.objects.filter(
            event=event, status=ApplicantStatusTypes.rejected.value
        )
        return [wish.applicant for wish in acceptable_wishes]

    @staticmethod
    def for_user_and_edition(user, edition):
        """
        Get applicant object corresponding to an user for given edition. If no
        applicant has been created for this edition yet, it will be created.
        """
        applicant, created = Applicant.objects.get_or_create(
            user=user, edition=edition
        )

        if created:
            applicant.save()

        return applicant

    def __str__(self):
        return str(self.user) + '@' + str(self.edition)

    class AlreadyLocked(Exception):
        """
        This exception is raised if a new application is submitted for an user
        who has already been accepted or rejected this year.
        """

        pass

    class Meta:
        unique_together = (('user', 'edition'),)


class EventWish(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = EnumField(
        ApplicantStatusTypes,
        db_index=True,
        blank=True,
        default=ApplicantStatusTypes.incomplete.value,
    )

    # Priority defined by the candidate to express his preferred event
    # The lower the order is, the more important is the choice
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} for {}'.format(str(self.applicant), str(self.event))

    class Meta:
        ordering = ('order',)
        unique_together = (('applicant', 'event'),)


@ChoiceEnum.labels(str.capitalize)
class AnswerTypes(ChoiceEnum):
    boolean = 0
    integer = 1
    date = 2
    string = 3
    text = 4
    multichoice = 5


class Form(models.Model):
    # Name of the form
    name = models.CharField(max_length=64)
    # List of question
    question_list = models.ManyToManyField(
        'Question', through='QuestionForForm'
    )

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    A generic question type, that can be of several type.

    If response_type is multichoice you have to specify the answer in the meta
    field, respecting the following structure:
    {
        "choices": {
            "0": "first option",
            "1": "second option"
        }
    }
    """

    # Formulation of the question
    question = models.TextField()
    # Potential additional indications about the questions
    comment = models.TextField(blank=True)
    # How to represent the answer
    response_type = EnumField(AnswerTypes)

    # If set to true, the applicant will need to fill this field in order to
    # save his application.
    always_required = models.BooleanField(default=False)
    # If set to true, the applicant will need to fill this field in order to
    # validate his application.
    finaly_required = models.BooleanField(default=True)

    # Some extra constraints on the answer
    meta = JSONField(encoder=DjangoJSONEncoder, default=dict, null=True)

    def __str__(self):
        ret = self.question

        if self.finaly_required:
            ret += ' (*)'

        return ret


class QuestionForForm(SortableMixin):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(
        default=0, editable=False, db_index=True
    )

    class Meta:
        ordering = ['order']


class Answer(models.Model):
    applicant = models.ForeignKey(
        Applicant, related_name='answers', on_delete=models.CASCADE
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = JSONField(encoder=DjangoJSONEncoder)

    def is_valid(self):
        '''
        Check if an answer is valid, a checkbox with required beeing true must
        be checked, and other kind of fields must necessary be filled.
        '''
        if not self.question.finaly_required:
            return True

        return bool(self.response)

    def __str__(self):
        if self.question.response_type == AnswerTypes.multichoice.value:
            if str(self.response) not in self.question.meta['choices']:
                return ''

            return self.question.meta['choices'][str(self.response)]

        return str(self.response)

    class Meta:
        unique_together = (('applicant', 'question'),)


class SubscriberEmail(models.Model):
    email = models.EmailField()
    date = models.DateTimeField(auto_now_add=True)

    @property
    def unsubscribe_token(self):
        subscriber_id = str(self.id).encode()
        secret = settings.SECRET_KEY.encode()
        return hashlib.sha256(subscriber_id + secret).hexdigest()[:32]

    @property
    def unsubscribe_url(self):
        return reverse(
            'gcc:news_unsubscribe',
            kwargs={'email': self.email, 'token': self.unsubscribe_token},
        )

    def __str__(self):
        return self.email


class SponsorQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Sponsor(AddressableModel, ContactModel, models.Model):
    def upload_logo_to(self, *args, **kwargs):
        return upload_path('sponsor')(self, *args, **kwargs)

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    logo = models.ImageField(upload_to=upload_logo_to, blank=True)
    site = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = SponsorQuerySet.as_manager()

    def __str__(self):
        return self.name
