# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.conf import settings
from django.contrib import messages, auth
from django.http import Http404
from django.http.response import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from rules.contrib.views import PermissionRequiredMixin

import users.forms
import users.models


def auto_login(request, user):
    # Auto-login bullshit because we don't want to write our own backend
    if not hasattr(user, 'backend'):
        for backend in settings.AUTHENTICATION_BACKENDS:
            if user == auth.load_backend(backend).get_user(user.pk):
                user.backend = backend
                break
    if hasattr(user, 'backend'):
        auth.login(request, user)
        return True
    return False


class AnonymousRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


@method_decorator([require_POST, csrf_protect, never_cache], name='dispatch')
class LogoutView(auth.views.LogoutView):
    next_page = reverse_lazy('gcc:index')


class ProfileView(DetailView):
    model = auth.get_user_model()
    context_object_name = 'shown_user'
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown_user = context[self.context_object_name]
        context['see_private'] = (
            self.request.user == shown_user or self.request.user.is_staff
        )
        return context

    def get(self, request, *args, **kwargs):
        result = super().get(request, *args, **kwargs)
        if not self.object.is_active and not self.request.user.is_staff:
            raise Http404()
        return result


class EditUserView(PermissionRequiredMixin, UpdateView):
    model = auth.get_user_model()
    form_class = users.forms.UserProfileForm
    template_name = 'users/edit.html'
    context_object_name = 'edited_user'
    permission_required = 'users.edit'

    def get_success_url(self):
        return reverse('users:edit', args=[self.get_object().pk])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _("Changes saved."))
        return super().form_valid(form)


class PasswordFormMixin:
    """
    SetPasswordForm prototype is (user, *args, **kwargs) and does not use
    'instance' kwarg.  “Because fuck logic, that's why.”
        — Django
    """

    form_class = auth.forms.PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        return kwargs

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.get_object(), **self.get_form_kwargs())

class UnsubscribeView(View):
    def get_user_token(self, req_params):
        try:
            user_id = req_params['uid']
            token = req_params['token']
        except KeyError:
            raise Http404()
        User = auth.get_user_model()
        u = get_object_or_404(User, pk=user_id)
        if not compare_digest(token, u.unsubscribe_token):
            raise Http404()
        return u, token

    def get(self, request, *args, **kwargs):
        user, token = self.get_user_token(request.GET)
        return render(request, 'users/unsubscribe.html',
                      {'unsubscribe_user': user, 'unsubscribe_token': token})

    def post(self, request, *args, **kwargs):
        user, _ = self.get_user_token(request.POST)
        user.allow_mailing = False
        user.save()
        return render(request, 'users/unsubscribe_confirm.html',
                      {'unsubscribe_user': user})
