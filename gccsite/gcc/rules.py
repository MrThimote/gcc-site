# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import rules

from gcc.models import Corrector, Event


@rules.predicate
def can_edit_own_application(user, applicant):
    return not applicant.is_locked()


@rules.predicate
def can_edit_application_labels(user, applicant):
    """
    This permission is granted if the corrector is allowed to review for an
    event the applicant applies to.
    """
    return Event.objects.filter(
        correctors__user=user, applicants=applicant
    ).exists()


@rules.predicate
def can_accept_wish(user, wish):
    return can_review_event(user, wish.event)


@rules.predicate
def can_review_event(user, event):
    return Corrector.objects.filter(event=event, user=user).exists()


rules.add_perm('gcc.can_edit_own_application', can_edit_own_application)
rules.add_perm('gcc.can_edit_application_labels', can_edit_application_labels)
rules.add_perm('gcc.can_accept_wish', can_accept_wish)
rules.add_perm('gcc.can_review', rules.is_staff)
rules.add_perm('gcc.can_review_event', can_review_event)
