# Copyright (C) <2019> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

import centers.models
import traceback
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from geopy.exc import GeopyError


class ContactInlineAdmin(admin.TabularInline):
    model = centers.models.Contact


class CenterAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'type', 'city')
    list_display = (
        'name',
        'city',
        'type',
        'coordinates',
        'is_active',
        'contact_names',
    )
    actions = ('geocode_centers', 'normalize_centers')
    search_fields = ('name', 'city', 'comments')
    inlines = [ContactInlineAdmin]

    def contact_names(self, obj):
        return ', '.join(c.get_full_name() for c in obj.contacts.all())

    def geocode_centers(self, request, queryset):
        success = 0
        errors = 0
        for center in queryset:
            try:
                center.geocode(suffix=', FRANCE')
                success += 1
            except GeopyError:
                errors += 1
        self.message_user(
            request,
            "{success} centers geocoded, {errors} errors".format(
                success=success, errors=errors
            ),
        )

    geocode_centers.short_description = _("Geocode selected centers")

    def normalize_centers(self, request, queryset):
        success = 0
        errors = 0
        for center in queryset:
            try:
                center.normalize(suffix=', FRANCE')
                success += 1
            except (GeopyError, ValueError):
                traceback.print_exc()
                errors += 1
        self.message_user(
            request,
            "{success} centers normalized, {errors} errors".format(
                success=success, errors=errors
            ),
        )

    normalize_centers.short_description = _(
        "Normalize selected center addresses"
    )


admin.site.register(centers.models.Center, CenterAdmin)
