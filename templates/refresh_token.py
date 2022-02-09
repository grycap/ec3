#!/usr/bin/env python
#
# CLUES - Cluster Energy Saving System
# Copyright (C) 2015 - GRyCAP - Universitat Politecnica de Valencia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import json
import re
import base64
import requests
import time
import os


class JWT(object):

    @staticmethod
    def b64d(b):
        """Decode some base64-encoded bytes.

        Raises Exception if the string contains invalid characters or padding.

        :param b: bytes
        """

        cb = b.rstrip(b"=")  # shouldn't but there you are

        # Python's base64 functions ignore invalid characters, so we need to
        # check for them explicitly.
        b64_re = re.compile(b"^[A-Za-z0-9_-]*$")
        if not b64_re.match(cb):
            raise Exception(cb, "base64-encoded data contains illegal characters")

        if cb == b:
            b = JWT.add_padding(b)

        return base64.urlsafe_b64decode(b)

    @staticmethod
    def add_padding(b):
        # add padding chars
        m = len(b) % 4
        if m == 1:
            # NOTE: for some reason b64decode raises *TypeError* if the
            # padding is incorrect.
            raise Exception(b, "incorrect padding")
        elif m == 2:
            b += b"=="
        elif m == 3:
            b += b"="
        return b

    @staticmethod
    def get_info(token):
        """
        Unpacks a JWT into its parts and base64 decodes the parts
        individually, returning the part 1 json decoded, where the
        token info is stored.

        :param token: The JWT token
        """
        part = tuple(token.encode("utf-8").split(b"."))
        part = [JWT.b64d(p) for p in part]
        return json.loads(part[1].decode("utf-8"))

class RefreshToken:

    REFRESH_TOKEN_FILE = "/usr/local/ec3/refresh.dat"

    def __init__(self, client_id, client_secret):
        self._refresh_time_diff = 600
        self._client_id = client_id
        self._client_secret = client_secret

    def _save_token(self, token):
        with open(self.REFRESH_TOKEN_FILE, 'w') as f:
            f.write(token)
        os.chmod(self.REFRESH_TOKEN_FILE, 0o600)

    def _load_token(self):
        try:
            with open(self.REFRESH_TOKEN_FILE, 'r') as f:
                return f.read()
        except:
            return None

    def get_refresh_token(self, access_token):
        """
        Get the access_token and refresh_token of the plugin client
        """
        try:
            decoded_token = JWT().get_info(access_token)
            token_scopes = "openid profile offline_access eduperson_entitlement"
            url = "%s/token" % decoded_token['iss']
            payload = ("client_id=%s&client_secret=%s&grant_type=urn%%3Aietf%%3Aparams%%3Aoauth%%3Agrant-type%%3Atoken-exchange&"
                        "audience=tokenExchange&subject_token_type=urn%%3Aietf%%3Aparams%%3Aoauth%%3Atoken-type%%3Aaccess_token&"
                        "subject_token=%s&scope=%s") % (self._client_id, self._client_secret,
                                                         access_token, token_scopes)
            headers = dict()
            headers['content-type'] = 'application/x-www-form-urlencoded'
            resp = requests.request("POST", url, data=payload, headers=headers, verify=False)
            if resp.status_code == 200:
                info = resp.json()
                refresh_token = info["refresh_token"]
                access_token = info["access_token"]
                print("Refresh token successfully obtained")
                self._save_token(refresh_token)
                return refresh_token, access_token
            else:
                print("Error getting refresh token: Code %d. Message: %s" % (resp.status_code, resp.text))
                return None, None
        except Exception as ex:
            print("Error getting refresh token: %s" % ex)
            return None, None

    def refresh_access_token(self, access_token, refresh_token):
        """
        Refresh the current access_token
        """
        try:
            decoded_token = JWT().get_info(access_token)
            token_scopes = "openid profile offline_access email eduperson_entitlement"
            url = "%s/token" % decoded_token['iss']
            payload = ("client_id=%s&client_secret=%s&grant_type=refresh_token&scope=%s"
                        "&refresh_token=%s") % (self._client_id, self._client_secret,
                                                token_scopes, refresh_token)
            headers = dict()
            headers['content-type'] = 'application/x-www-form-urlencoded'
            resp = requests.request("POST", url, data=payload, headers=headers, verify=False)
            if resp.status_code == 200:
                info = resp.json()
                access_token = info["access_token"]
                print("Access token successfully refreshed.")
                return access_token
            else:
                print("Error refreshing access token: Code %d. Message: %s" % (resp.status_code, resp.text))
                return None
        except Exception as ex:
            print("Error refreshing access token: %s" % ex)
            return None


    def is_access_token_to_expire(self, access_token):
        """
        Check if the current access token is to expire
        """
        try:
            decoded_token = JWT().get_info(access_token)
            now = int(time.time())
            expires = int(decoded_token['exp'])
            print("The access token is valid for %s seconds." % (expires - now))
            if expires - now < self._refresh_time_diff:
                return True
            else:
                return False
        except Exception as ex:
            print("Error getting token info: %s" % ex)
            return False

    def get_token_from_auth_file(self, auth_file):
        with open(auth_file, 'r') as f:
            auth_data = f.read()

        for line in auth_data.split("\n"):
            if "OpenStack" in line:
                for token in line.split(";"):
                    if token.strip().startswith("password"):
                        return token.split("=")[1].strip().strip("'")

            if "InfrastructureManager" in line:
                for token in line.split(";"):
                    if token.strip().startswith("token"):
                        return token.split("=")[1].strip().strip("'")

        return None

    def save_token_to_auth_file(self, auth_file, access_token):
        with open(auth_file, 'r') as f:
            auth_data = f.read()

        # replace old token with new one
        new_auth = ""
        for line in auth_data.split("\n"):
            if "3.x_oidc_access_token" in line:
                pos_ini = line.find("password = ") + 11
                new_auth += line[:pos_ini] + access_token
                pos_end = max(line.find(";", pos_ini), line.find("\n", pos_ini))
                if pos_end > -1:
                    new_auth += line[pos_end:]
                new_auth += "\n"
            elif "InfrastructureManager" in line and "token = " in line:
                pos_ini = line.find("token = ") + 8
                new_auth += line[:pos_ini] + access_token
                pos_end = max(line.find(";", pos_ini), line.find("\n", pos_ini))
                if pos_end > -1:
                    new_auth += line[pos_end:]
                new_auth += "\n"
            else:
                new_auth += line + "\n"

        with open(auth_file, 'w') as f:
            f.write(new_auth)

if __name__ == "__main__":
    client_id = sys.argv[1]
    client_secret = sys.argv[2]

    rt = RefreshToken(client_id, client_secret)
    access_token = rt.get_token_from_auth_file("/usr/local/ec3/auth.dat")
    refresh_token = rt._load_token()

    if not access_token:
        print("Error reading access token.")
        sys.exit(1)
    if not refresh_token:
        refresh_token, access_token = rt.get_refresh_token(access_token)
        if not access_token:
            print("Error getting refresh token.")
            sys.exit(1)
        rt.save_token_to_auth_file("/usr/local/ec3/auth.dat", access_token)
    elif rt.is_access_token_to_expire(access_token):
        access_token = rt.refresh_access_token(access_token, refresh_token)
        if not access_token:
            print("Error getting refresh token.")
            sys.exit(1)
        rt.save_token_to_auth_file("/usr/local/ec3/auth.dat", access_token)
    else:
        print("Access token valid. Nothing to do.")
        sys.exit(0)
    
    
