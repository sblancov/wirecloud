# -*- coding: utf-8 -*-

# Copyright (c) 2013-2015 Conwet Lab., Universidad Politécnica de Madrid

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

"""
FIWARE IdM OAuth2 support.

This contribution adds support for FIWARE IdM OAuth2 service. The settings
FIWARE_APP_ID and FIWARE_APP_SECRET must be defined with the values
given by FIWARE IdM application registration process.

Extended permissions are supported by defining FIWARE_EXTENDED_PERMISSIONS
setting, it must be a list of values to request.

By default account id and token expiration time are stored in extra_data
field, check OAuthBackend class for details on how to extend it.
"""

import base64
import json
import requests
from six.moves.urllib.parse import urljoin

from django.conf import settings

from social.backends.oauth import BaseOAuth2


FIWARE_LAB_IDM_SERVER = 'https://account.lab.fiware.org'

FIWARE_AUTHORIZATION_ENDPOINT = 'oauth2/authorize'
FIWARE_ACCESS_TOKEN_ENDPOINT = 'oauth2/token'
FIWARE_USER_DATA_ENDPOINT = 'user'


class FIWAREOAuth2(BaseOAuth2):
    """FIWARE IdM OAuth authentication backend"""
    name = 'fiware'
    ID_KEY = 'username'
    AUTHORIZATION_URL = urljoin(getattr(settings, 'FIWARE_IDM_SERVER', FIWARE_LAB_IDM_SERVER), FIWARE_AUTHORIZATION_ENDPOINT)
    ACCESS_TOKEN_URL = urljoin(getattr(settings, 'FIWARE_IDM_SERVER', FIWARE_LAB_IDM_SERVER), FIWARE_ACCESS_TOKEN_ENDPOINT)
    USER_DATA_URL = urljoin(getattr(settings, 'FIWARE_IDM_SERVER', FIWARE_LAB_IDM_SERVER), FIWARE_USER_DATA_ENDPOINT)
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_VAR_NAME = 'FIWARE_EXTENDED_PERMISSIONS'
    EXTRA_DATA = [
        ('username', 'username'),
        ('refresh_token', 'refresh_token'),
        ('expires_in', 'expires_in'),
    ]

    def auth_headers(self):
        return {
            'Authorization': 'Basic {0}'.format(base64.urlsafe_b64encode(
                ('{0}:{1}'.format(*self.get_key_and_secret()).encode())
            ))
        }

    def get_user_details(self, response):
        """Return user details from FIWARE account"""
        name = response.get('displayName') or ''
        first_name = ''
        last_name = ''
        if ' ' in name:
            first_name, last_name = name.split(' ', 1)
        else:
            first_name = name
        return {'username': response.get('username'),
                'email': response.get('email') or '',
                'fullname': name,
                'first_name': first_name,
                'last_name': last_name}

    @classmethod
    def request_user_info(cls, access_token):
        response = requests.get(cls.USER_DATA_URL, params={'access_token': access_token})
        response.raise_for_status()
        return json.loads(response.content)

    @classmethod
    def _user_data(cls, access_token):
        data = cls.request_user_info(access_token)
        # Newer versions of the FIWARE IdM provides and id field with the
        # username of the user. Older versions use actorId as identifier, but
        # also provides a nickName field. We use nickName because it is also
        # unique and provides a better way for migrating to newer versions
        # of KeyRock. Store the appropiated field in username to simplify
        # the rest of the code
        data['username'] = data['nickName'] if 'nickName' in data else data['id']

        return data

    def user_data(self, access_token, *args, **kwargs):
        return self._user_data(access_token)
