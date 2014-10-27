# -*- coding: utf-8 -*-

# Copyright 2008-2014 Universidad Politécnica de Madrid

# This file is part of Wirecloud.

# Wirecloud is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Wirecloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Wirecloud.  If not, see <http://www.gnu.org/licenses/>.

import json

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from wirecloud.commons.baseviews import Resource
from wirecloud.commons.utils.cache import no_cache
from wirecloud.commons.utils.http import authentication_required, build_error_response, supported_request_mime_types
from wirecloud.commons.utils.transaction import commit_on_http_success
from wirecloud.platform.models import PlatformPreference, WorkspacePreference, Tab, TabPreference, update_session_lang, Workspace


def update_preferences(user, preferences_json):
    _currentPreferences = PlatformPreference.objects.filter(user=user)
    currentPreferences = {}
    for currentPreference in _currentPreferences:
        currentPreferences[currentPreference.name] = currentPreference

    for name in preferences_json.keys():
        preference_data = preferences_json[name]

        if name in currentPreferences:
            preference = currentPreferences[name]
        else:
            preference = PlatformPreference(user=user, name=name)

        preference.value = unicode(preference_data['value'])
        preference.save()


def parseValues(values):
    _values = {}

    for value in values:
        _values[value.name] = {'inherit': False, 'value': value.value}

    return _values


def parseInheritableValues(values):
    _values = {}

    for value in values:
        _values[value.name] = {'inherit': value.inherit, 'value': value.value}

    return _values


def get_tab_preference_values(tab):
    return parseInheritableValues(TabPreference.objects.filter(tab=tab.pk))


def update_tab_preferences(tab, preferences_json):
    _currentPreferences = TabPreference.objects.filter(tab=tab)
    currentPreferences = {}
    for currentPreference in _currentPreferences:
        currentPreferences[currentPreference.name] = currentPreference

    for name in preferences_json.keys():
        preference_data = preferences_json[name]

        if name in currentPreferences:
            preference = currentPreferences[name]
        else:
            preference = TabPreference(tab=tab, name=name)

        if 'value' in preference_data:
            preference.value = unicode(preference_data['value'])

        if 'inherit' in preference_data:
            preference.inherit = preference_data['inherit']

        preference.save()

    tab.workspace.save()  # Invalidate workspace cache


def make_workspace_preferences_cache_key(workspace):
    return '_workspace_preferences_cache/%s/%s' % (workspace.id, workspace.last_modified)


def get_workspace_preference_values(workspace):

    cache_key = make_workspace_preferences_cache_key(workspace)
    values = cache.get(cache_key)
    if values is None:
        values = parseInheritableValues(workspace.workspacepreference_set.all())
        cache.set(cache_key, values)

    return values


def update_workspace_preferences(workspace, preferences_json, invalidate_cache=True):

    changes = False

    # Create a preference instance dict
    currentPreferences = {}
    for currentPreference in workspace.workspacepreference_set.all():
        currentPreferences[currentPreference.name] = currentPreference

    # Update preference values
    for name in preferences_json.keys():
        preference_data = preferences_json[name]
        pref_changes = False

        if name in currentPreferences:
            preference = currentPreferences[name]
        else:
            preference = WorkspacePreference(workspace=workspace, name=name)

        if 'value' in preference_data and preference.value != preference_data['value']:
            preference.value = preference_data['value']
            changes = pref_changes = True

        if 'inherit' in preference_data and preference.inherit != preference_data['inherit']:
            preference.inherit = preference_data['inherit']
            changes = pref_changes = True

        if pref_changes:
            preference.save()

    if invalidate_cache and changes:
        cache_key = make_workspace_preferences_cache_key(workspace)
        cache.delete(cache_key)
        workspace.save()  # Invalidate workspace cache


class PlatformPreferencesCollection(Resource):

    @no_cache
    def read(self, request):
        if request.user.is_authenticated():
            result = parseValues(PlatformPreference.objects.filter(user=request.user))
        else:
            result = {}

        return HttpResponse(json.dumps(result), content_type='application/json; charset=UTF-8')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    @commit_on_http_success
    def create(self, request):
        try:
            preferences_json = json.loads(request.body)
        except ValueError as e:
            msg = _("malformed json data: %s") % unicode(e)
            return build_error_response(request, 400, msg)

        update_preferences(request.user, preferences_json)

        if 'language' in preferences_json:
            update_session_lang(request, request.user)

        return HttpResponse(status=204)


class WorkspacePreferencesCollection(Resource):

    @authentication_required
    @no_cache
    def read(self, request, workspace_id):

        # Check Workspace existance and owned by this user
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        if not (request.user.is_superuser or workspace.users.filter(pk=request.user.pk).exists()):
            return build_error_response(request, 403, _('You are not allowed to read this workspace'))

        result = get_workspace_preference_values(workspace)

        return HttpResponse(json.dumps(result), content_type='application/json; charset=UTF-8')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    @commit_on_http_success
    def create(self, request, workspace_id):

        # Check Workspace existance and owned by this user
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        if not (request.user.is_superuser or workspace.users.filter(pk=request.user.pk).exists()):
            return build_error_response(request, 403, _('You are not allowed to update this workspace'))

        try:
            preferences_json = json.loads(request.body)
        except ValueError as e:
            msg = _("malformed json data: %s") % unicode(e)
            return build_error_response(request, 400, msg)

        if 'public' in preferences_json:
            workspace.public = preferences_json['public']['value']
            workspace.save()
            del preferences_json['public']

        update_workspace_preferences(workspace, preferences_json)

        return HttpResponse(status=204)


class TabPreferencesCollection(Resource):

    @authentication_required
    @no_cache
    def read(self, request, workspace_id, tab_id):

        # Check Tab existance and owned by this user
        tab = get_object_or_404(Tab.objects.select_related('workspace'), workspace__pk=workspace_id, pk=tab_id)
        if not (request.user.is_superuser or tab.workspace.users.filter(pk=request.user.pk).exists()):
            return build_error_response(request, 403, _('You are not allowed to read this workspace'))

        result = get_tab_preference_values(tab)

        return HttpResponse(json.dumps(result), content_type='application/json; charset=UTF-8')

    @authentication_required
    @supported_request_mime_types(('application/json',))
    @commit_on_http_success
    def create(self, request, workspace_id, tab_id):

        # Check Tab existance and owned by this user
        tab = get_object_or_404(Tab.objects.select_related('workspace'), workspace__pk=workspace_id, pk=tab_id)
        if not (request.user.is_superuser or tab.workspace.users.filter(pk=request.user.pk).exists()):
            return build_error_response(request, 403, _('You are not allowed to update this workspace'))

        try:
            preferences_json = json.loads(request.body)
        except ValueError as e:
            msg = _("malformed json data: %s") % unicode(e)
            return build_error_response(request, 400, msg)

        update_tab_preferences(tab, preferences_json)
        return HttpResponse(status=204)
