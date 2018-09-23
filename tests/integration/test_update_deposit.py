# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2017 CERN.
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
# or submit itself to any jurisdiction.

"""Integration tests for updating deposits."""

import json

from invenio_search import current_search
from pytest import mark

# #######################################
# # api/deposits/{pid}  [PUT]
# #######################################

def test_update_deposit_with_non_existing_pid_returns_404(app,
                                                          auth_headers_for_superuser):
    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format('non-existing-pid'),
                          headers=auth_headers_for_superuser,
                          data=json.dumps({}))

        assert resp.status_code == 404


def test_update_deposit_when_user_has_no_permission_returns_403(app,
                                                                users,
                                                                create_deposit,
                                                                json_headers,
                                                                auth_headers_for_user):
    deposit = create_deposit(users['lhcb_user'], 'lhcb-v0.0.1')
    other_user_headers = auth_headers_for_user(users['lhcb_user2'])

    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=other_user_headers + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 403


def test_update_deposit_when_user_is_owner_can_update_his_deposit(app,
                                                                  users,
                                                                  create_deposit,
                                                                  json_headers,
                                                                  auth_headers_for_user):
    owner = users['lhcb_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')

    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(owner) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 200



def test_update_deposit_when_superuser_can_update_others_deposits(app,
                                                                  users,
                                                                  create_deposit,
                                                                  json_headers,
                                                                  auth_headers_for_superuser):
    owner = users['lhcb_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')

    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_superuser + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 200


@mark.parametrize("action", [
    ("deposit-update"),
    ("deposit-admin")
])
def test_update_deposit_when_user_has_update_or_admin_access_can_update(action,
                                                                        app, db, users,
                                                                        create_deposit,
                                                                        json_headers,
                                                                        auth_headers_for_user):
    owner, other_user = users['lhcb_user'], users['cms_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')

    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(other_user) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 403

        permissions = [{
            'email': other_user.email,
            'type': 'user',
            'op': 'add',
            'action': action
        }]

        resp = client.post('/deposits/{}/actions/permissions'.format(deposit['_deposit']['id']),
                           headers=auth_headers_for_user(owner) + json_headers,
                           data=json.dumps(permissions))

        # sometimes ES needs refresh
        current_search.flush_and_refresh('deposits')
        
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(other_user) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 200


def test_update_deposit_when_user_has_only_read_access_returns_403(app, db, users,
                                                                   create_deposit,
                                                                   json_headers,
                                                                   auth_headers_for_user):
    owner, other_user = users['lhcb_user'], users['cms_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')

    with app.test_client() as client:
        permissions = [{
            'email': other_user.email,
            'type': 'user',
            'op': 'add',
            'action': 'deposit-read'
        }]

        resp = client.post('/deposits/{}/actions/permissions'.format(deposit['_deposit']['id']),
                           headers=auth_headers_for_user(owner) + json_headers,
                           data=json.dumps(permissions))

        # sometimes ES needs refresh
        current_search.flush_and_refresh('deposits')
        
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(other_user) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 403


@mark.parametrize("action", [
    ("deposit-update"),
    ("deposit-admin")
])
def test_update_deposit_when_user_is_member_of_egroup_that_has_update_or_admin_access_he_can_update(action,
                                                                                                    app, db, users,
                                                                                                    create_deposit,
                                                                                                    json_headers,
                                                                                                    auth_headers_for_user):
    owner, other_user = users['lhcb_user'], users['cms_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')

    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(other_user) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 403

        permissions = [{
            'email': 'cms-members@cern.ch',
            'type': 'egroup',
            'op': 'add',
            'action': action
        }]

        resp = client.post('/deposits/{}/actions/permissions'.format(deposit['_deposit']['id']),
                           headers=auth_headers_for_user(owner) + json_headers,
                           data=json.dumps(permissions))

        assert resp.status_code == 201

        # sometimes ES needs refresh
        current_search.flush_and_refresh('deposits')
        
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(other_user) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 200


def test_update_deposit_when_user_is_member_of_egroup_that_has_only_read_access_returns_403(app, db, users,
                                                                                            create_deposit,
                                                                                            json_headers,
                                                                                            auth_headers_for_user):
    owner, other_user = users['lhcb_user'], users['cms_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')

    with app.test_client() as client:
        permissions = [{
            'email': 'cms-members@cern.ch',
            'type': 'egroup',
            'op': 'add',
            'action': 'deposit-read'
        }]

        resp = client.post('/deposits/{}/actions/permissions'.format(deposit['_deposit']['id']),
                           headers=auth_headers_for_user(owner) + json_headers,
                           data=json.dumps(permissions))

        # sometimes ES needs refresh
        current_search.flush_and_refresh('deposits')
        
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(other_user) + json_headers,
                             data=json.dumps({}))

        assert resp.status_code == 403


# @TOFIX updating schema shouldnt be allowed
@mark.skip
def test_update_deposit_cannot_update_schema_field(app, db, users,
                                                   create_deposit,
                                                   create_schema,
                                                   json_headers,
                                                   auth_headers_for_user):
    owner = users['lhcb_user']
    deposit = create_deposit(owner, 'lhcb-v0.0.1')
    schema = create_schema('deposits/records/another-v0.0.0',
                           experiment='LHCb') 

    with app.test_client() as client:
        resp = client.put('/deposits/{}'.format(deposit['_deposit']['id']),
                             headers=auth_headers_for_user(owner) + json_headers,
                             data=json.dumps({
                                 '$schema': ''
                             }))

        assert resp.status_code == 400


#@TODO add tests to check if put validates properly
