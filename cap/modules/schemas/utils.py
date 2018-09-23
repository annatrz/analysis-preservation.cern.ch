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

"""Utils for Schemas module."""

import json

from invenio_db import db

from .errors import SchemaDoesNotExist
from .models import Schema


def add_or_update_schema(fullpath=None, data=None):
    """Add or update schema by fullpath, e.g. records/ana1-v0.0.1.json."""
    try:
        schema = Schema.get_by_fullpath(fullpath)
        schema.experiment = data.get('experiment', None)
        schema.fullname = data.get('fullname', None)
        schema.json = data['jsonschema']

        print('{} updated.'.format(fullpath))

    except SchemaDoesNotExist:
        schema = Schema(fullpath=fullpath,
                        experiment=data.get('experiment', None),
                        fullname=data.get('fullname', None),
                        json=json.dumps(data['jsonschema']))

        # @TODO on schema save add experiments permissions
        db.session.add(schema)

        print('{} added.'.format(fullpath))

    db.session.commit()
