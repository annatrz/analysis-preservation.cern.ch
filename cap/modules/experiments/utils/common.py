# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016 CERN.
#
# CERN Analysis Preservation Framework is free software; you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Analysis Preservation Framework is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Analysis Preservation Framework; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Experiments common utils."""


import subprocess
from functools import wraps
from os.path import join

import cern_sso
from cachetools.func import ttl_cache
from flask import current_app


def kinit(principal, keytab):
    """Run a function with given kerberos credentials.

    Steps:
    * kinit
    * call function
    * kdestroy

    Location of keytab files defined in `cap.config.KEYTABS_LOCATION`.

    :param str principal: Kerberos principal, e.g. user@CERN.CH
    :param str keytab: Keytab filename, e.g. user.keytab
    """
    def decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            kt = join(current_app.config.get('KEYTABS_LOCATION'), keytab)

            subprocess.check_output(
                'kinit -kt {} {}'.format(kt, principal), shell=True)
            ret_val = func(*args, **kwargs)
            subprocess.check_output(
                'kdestroy -p {}'.format(principal), shell=True)

            return ret_val
        return wrapped_function
    return decorator


@ttl_cache(ttl=86000)  # cookie expires after 24 hours
def generate_krb_cookie(principal, kt, url):
    """Generate a HTTP cookie with given kerberos credentials.

    :param str principal: Kerberos principal, e.g. user@CERN.CH
    :param str kt: Keytab filename e.g user.keytab
    :param str url: URL

    :returns: Generated HTTP Cookie
    :rtype `requests.cookies.RequestsCookieJar`
    """
    @kinit(principal, kt)
    def generate(url):
        cookie = cern_sso.krb_sign_on(url)
        return cookie

    return generate(url)
