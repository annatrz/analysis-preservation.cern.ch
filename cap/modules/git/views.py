# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2018 CERN.
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
"""Git module views."""

from __future__ import absolute_import, print_function

from flask import Blueprint, abort, jsonify, request
from invenio_db import db
from sqlalchemy.orm.exc import NoResultFound

from .errors import GitRequestWithInvalidSignature
from .factory import create_git_api
from .models import GitRepository, GitSnapshot, GitWebhook
from .serializers import payload_serializer_factory
from .tasks import download_repo

git_bp = Blueprint('cap_git', __name__, url_prefix='/repos')


@git_bp.route('/event', methods=['POST'])
def get_webhook_event():
    """The route that webhooks will use to update the repo information."""

    payload = request.get_json()
    payload.update(request.headers)  # info about type of event inside headers
    serializer = payload_serializer_factory()

    if not serializer:
        abort(403)

    try:
        data = serializer.dump(payload).data
    except Exception:
        abort(400, 'Server was unable to serialize this request')

    if data["event_type"] == 'ping':
        return jsonify({'message': 'Got it.'})

    try:
        repo = GitRepository.query.filter_by(
            host=data.pop('host'), external_id=data.pop('repo_id')).one()

        webhook = GitWebhook.query.filter_by(event_type=data["event_type"],
                                             branch=data['branch'],
                                             repo_id=repo.id).one()
    except NoResultFound:
        abort(404, 'This webhook was not registered in our system.')

    for subscriber in webhook.subscribers:
        # api client with subscriber token
        api = create_git_api(repo.host, repo.owner, repo.name, webhook.branch,
                             subscriber.user_id)
        try:
            api.verify_request(webhook.secret)
        except GitRequestWithInvalidSignature:
            abort(403)

        if webhook.branch:
            filename = f'repositories/{api.host}/{api.owner}/{api.repo}' \
                       f'/{webhook.branch}.tar.gz'
        else:
            filename = f'repositories/{api.host}/{api.owner}/{api.repo}.tar.gz'

        download_repo.delay(
            str(subscriber.record_id),
            filename,
            api.get_repo_download(),
            api.auth_headers,
        )

        db.session.add(GitSnapshot(payload=data, webhook_id=webhook.id))
        db.session.commit()

    return jsonify({'message': 'Snapshot of repository was saved.'})
