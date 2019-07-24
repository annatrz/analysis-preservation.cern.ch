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

"""Views for schemas."""

from flask import Blueprint, abort, jsonify, request
from flask.views import MethodView
from flask_login import current_user
from invenio_db import db
from invenio_jsonschemas.errors import JSONSchemaNotFound

from cap.modules.access.utils import login_required

from .models import Schema
from .permissions import AdminSchemaPermission, ReadSchemaPermission
from .utils import get_schemas_for_user

blueprint = Blueprint(
    'cap_schemas',
    __name__,
    url_prefix='/jsonschemas',
)


EDITABLE_FIELDS = [
    'fullname',
    'use_deposit_as_record',
    #   TODO can be editable, but create/remove es index on edit
    #   'is_indexed',
    'deposit_mapping',
    'record_mapping',
    'deposit_options',
    'record_options'
]


class SchemaAPI(MethodView):
    """CRUD views for Schema model."""

    decorators = [login_required]

    def get(self, name=None, version=None):
        """Get all schemas that user has access to."""
        if name:
            try:
                if version:
                    schema = Schema.get(name, version)
                else:
                    schema = Schema.get_latest(name)
            except JSONSchemaNotFound:
                abort(404)

            if not ReadSchemaPermission(schema).can():
                abort(403)

            response = schema.serialize()

        else:
            schemas = get_schemas_for_user()
            response = [schema.serialize() for schema in schemas]

        return jsonify(response)

    def post(self):
        """Create new schema."""
        data = request.json

        schema = Schema(**data)
        schema.give_admin_access_for_user(current_user)
        db.session.add(schema)
        db.session.commit()

        return jsonify(schema.serialize())

    def put(self, name, version):
        """Update schema."""
        try:
            schema = Schema.get(name, version)
        except JSONSchemaNotFound:
            abort(404)

        data = request.json

        with AdminSchemaPermission(schema).require(403):

            # only editable fields can be updated
            valid_data = {k: v for k, v in data.iteritems()
                          if k in EDITABLE_FIELDS}

            schema.update(**valid_data)
            db.session.commit()

            return jsonify(schema.serialize())

    def delete(self, name, version):
        """Delete schema."""
        try:
            schema = Schema.get(name, version)
        except JSONSchemaNotFound:
            abort(404)

        with AdminSchemaPermission(schema).require(403):
            db.session.delete(schema)
            db.session.commit()

            return 'Schema deleted.', 204


schema_view_func = SchemaAPI.as_view('schemas')

blueprint.add_url_rule('/',
                       defaults={'name': None, 'version': None},
                       view_func=schema_view_func, methods=['GET', ])
blueprint.add_url_rule('/',
                       view_func=schema_view_func, methods=['POST', ])
blueprint.add_url_rule('/<string:name>',
                       view_func=schema_view_func,
                       methods=['GET', ])
blueprint.add_url_rule('/<string:name>/<string:version>',
                       view_func=schema_view_func,
                       methods=['GET', 'PUT', 'DELETE'])