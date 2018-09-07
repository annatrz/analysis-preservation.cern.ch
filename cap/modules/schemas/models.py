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

"""Models for JSONschemas."""

import re

from invenio_access.models import ActionRoles
from invenio_db import db
from invenio_search import current_search
from invenio_search import current_search_client as es
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils.types import JSONType

from .errors import SchemaDoesNotExist
from .permissions import SchemaReadAction


class Schema(db.Model):
    """Model defining analysis JSON schemas."""

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), unique=False, nullable=False)
    full_name = db.Column(db.String(128), unique=False, nullable=True)

    experiment = db.Column(db.String(128), unique=False, nullable=True)

    experiment_full_name = db.Column(
        db.String(128), unique=False, nullable=True)

    # version
    major = db.Column(db.Integer, unique=False, nullable=False)
    minor = db.Column(db.Integer, unique=False, nullable=False, default=0)
    patch = db.Column(db.Integer, unique=False, nullable=False, default=0)

    partial = db.Column(db.Boolean(create_constraint=False),
                        unique=False,
                        default=False)

    json = db.Column(
        JSONType().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ),
        default=lambda: dict(),
        nullable=True
    )

    __tablename__ = 'schema'
    __table_args__ = (UniqueConstraint('name', 'major', 'minor', 'patch',
                                       name='unique_schema_version'),)

    def __init__(self, **kwargs):
        super(Schema, self).__init__(**kwargs)

    @property
    def version(self):
        """Return stringified version."""
        return "{}.{}.{}".format(self.major, self.minor, self.patch)

    @property
    def index_name(self):
        return "{}-v{}".format(self.name.replace('/', '-'), self.version)

    @property
    def aliases(self):
        aliases = []
        if self.name.startswith('deposits'):
            aliases = ['deposits', 'deposits-records']
        elif self.name.startswith('records'):
            aliases = ['records']
        return aliases

    def is_record(self):
        return self.name.startswith('records')

    def add_read_access(self, role):
        db.session.add(
            ActionRoles.allow(
                SchemaReadAction(self.id),
                role=role
            )
        )
        db.session.commit()

    @classmethod
    def get_latest(cls, name):
        """Get the latest version of schema with given name."""
        try:
            return cls.query \
                .filter_by(name=name) \
                .order_by(cls.major.desc(),
                          cls.minor.desc(),
                          cls.patch.desc())\
                .first()
        except NoResultFound:
            raise SchemaDoesNotExist

    @classmethod
    def get_by_fullstring(cls, string):
        """Get schema by fullstring, e.g. record/schema-v0.0.1.json."""
        regex = re.compile('(?:.*schemas)?'
                           '/?(?P<name>\S+)'
                           '-v(?P<major>\d+).'
                           '(?P<minor>\d+).'
                           '(?P<patch>\d+)'
                           '(?:.json)?')
        name, major, minor, patch = re.search(regex, string).groups()

        try:
            return cls.query \
                .filter_by(name=name,
                           major=major,
                           minor=minor,
                           patch=patch)\
                .one()
        except NoResultFound:
            raise SchemaDoesNotExist

    @classmethod
    def get_schemas(cls):
        """Get available schemas."""
        available_schemas = cls.query.filter(cls.experiment.isnot(
            None), cls.name.startswith('deposits/records')).all()

        return ["{}-v{}.{}.{}.json".format(
            i.name, i.major, i.minor, i.patch)
            for i in available_schemas]

    @classmethod
    def get_experiments(cls):
        """Get available experiments."""
        experiments = cls.query.filter(cls.experiment.isnot(
            None), cls.name.startswith('deposits/records')).all()

        return [exp.experiment for exp in experiments]

    @classmethod
    def get_results(cls):
        """Return all rows with schemas."""
        return cls.query.filter(cls.experiment.isnot(None),
                                cls.name.startswith('deposits/records')).all()

@event.listens_for(Schema, 'after_insert')
def after_insert_schema(target, value, initiator):
    if not initiator.partial:
        # invenio search needs it
        current_search.mappings[initiator.index_name] = {}

        if not es.indices.exists(initiator.index_name):
            es.indices.create(
                index=initiator.index_name,
                body={},
                ignore=False
            )

            for alias in initiator.aliases:
                es.indices.update_aliases({
                    "actions": [
                        {"add": {"index": initiator.index_name, "alias": alias}}
                    ]
                })


@event.listens_for(Schema, 'after_delete')
def before_delete_schema(mapper, connect, target):
    if es.indices.exists(target.index_name):
        es.indices.delete(target.index_name)

    # invenio search needs it
    current_search.mappings.pop(target.index_name)
