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
"""CAP Deposit loaders."""

from copy import deepcopy

from flask import current_app, request
from invenio_rest.errors import FieldError
from jsonschema import Draft4Validator, FormatChecker, validators
from jsonschema.exceptions import ValidationError

from cap.modules.deposit.utils import clean_empty_values
from cap.modules.schemas.resolvers import (resolve_schema_by_url,
                                           schema_name_to_url)

all_validators = dict(Draft4Validator.VALIDATORS)


def validate_das_dataset(validator, value, instance, schema):
    import ipdb
    ipdb.set_trace()
    pass


all_validators['validate-with-das'] = validate_with_das

MyValidator = validators.extend(Draft4Validator, validators=all_validators)


def json_v1_loader(data=None):
    """Load data from request and process URLs."""
    data = deepcopy(data or request.get_json())

    # remove underscore prefixed fields
    data = {k: v for k, v in data.items() if not k.startswith('_')}

    result = clean_empty_values(data)

    return result
