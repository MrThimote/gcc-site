# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import hashlib

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from gcc.models import Applicant, ApplicantStatusTypes
from prologin.models import (
    AddressableModel,
    ChoiceEnum,
    EnumField,
    GenderField,
)
from timezone_field import TimeZoneField


class EducationStage(ChoiceEnum):
    middle_school = (0, _("Middle school"))
    high_school = (1, _("High school"))
    bac = (2, _("Bac"))
    bacp1 = (3, _("Bac+1"))
    bacp2 = (4, _("Bac+2"))
    bacp3 = (5, _("Bac+3"))
    bacp4 = (6, _("Bac+4"))
    bacp5 = (7, _("Bac+5"))
    bacp6 = (8, _("Bac+6 and after"))
    other = (9, _("Other"))
    former = (10, _("Former student"))

    @classmethod
    def _get_choices(cls):
        return tuple(m.value for m in cls)


class GCCUser(AbstractUser, AddressableModel):
    @staticmethod
    def upload_seed(instance):
        return 'prologinuser/{}'.format(instance.pk).encode()

    # user have to be imported by the oauth client
    id = models.IntegerField(primary_key=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    gender = GenderField(blank=True, null=True, db_index=True)

    school_stage = EnumField(
        EducationStage,
        null=True,
        db_index=True,
        blank=True,
        verbose_name=_("Educational stage"),
    )

    phone = models.CharField(
        max_length=16, blank=True, verbose_name=_("Phone")
    )

    birthday = models.DateField(
        blank=True, null=True, verbose_name=_("Birth day")
    )

    allow_mailing = models.BooleanField(
        default=True,
        blank=True,
        db_index=True,
        verbose_name=_("Allow Girls Can Code! to send me emails"),
        help_text=_(
            "We only mail you to provide useful information during the "
            "various stages of the contest. We hate spam as much as "
            "you do!"
        ),
    )

    signature = models.TextField(blank=True, verbose_name=_("Signature"))

    timezone = TimeZoneField(
        default=settings.TIME_ZONE, verbose_name=_("Time zone")
    )

    preferred_locale = models.CharField(
        max_length=8,
        blank=True,
        verbose_name=_("Locale"),
        choices=settings.LANGUAGES,
    )

    @cached_property
    def participations_count(self):
        """The number of times this user has been to an event."""
        applicants = Applicant.objects.filter(user=self)
        return sum(
            (applicant.status == ApplicantStatusTypes.confirmed.value)
            for applicant in applicants
        )

    @property
    def unsubscribe_token(self):
        """The token used to unsubscribe from the mailing lists."""
        user_id = str(self.id).encode()
        secret = settings.SECRET_KEY.encode()
        return hashlib.sha256(user_id + secret).hexdigest()

    def has_partial_address(self):
        """Return if the user has filled part of their address fields."""
        return any((self.address, self.city, self.country, self.postal_code))

    def has_complete_address(self):
        """Return if the user has filled their complete address."""
        return all((self.address, self.city, self.country, self.postal_code))

    def has_complete_profile(self):
        """Return if the user's profile is complete."""
        return self.has_complete_address() and all(
            (
                self.first_name,
                self.last_name,
                self.email,
                self.gender,
                self.birthday,
                self.phone,
            )
        )

    def get_absolute_url(self):
        """Return the url for this user's profile."""
        return reverse('users:profile', args=[self.pk])

    def get_unsubscribe_url(self):
        """Return the email unsubscribe url for this user."""
        return '{}{}?uid={}&token={}'.format(
            settings.SITE_BASE_URL,
            reverse('users:unsubscribe'),
            self.id,
            self.unsubscribe_token,
        )
