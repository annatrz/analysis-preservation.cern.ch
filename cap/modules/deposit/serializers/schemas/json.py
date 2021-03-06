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
"""CAP Basic Schemas."""

import copy

from marshmallow import Schema, fields

from cap.modules.deposit.permissions import (AdminDepositPermission,
                                             UpdateDepositPermission)
from cap.modules.records.serializers.schemas import common
from cap.modules.repos.serializers import (GitSnapshotSchema,
                                           GitWebhookSubscriberSchema)
from cap.modules.workflows.serializers import ReanaWorkflowSchema
from invenio_jsonschemas import current_jsonschemas


class DepositSchema(common.CommonRecordSchema):
    """Schema for deposit v1 in JSON."""
    type = fields.Str(default='deposit')

    recid = fields.Str(attribute='metadata._deposit.pid.value',
                       dump_only=True)  # only for published ones

    cloned_from = fields.Dict(attribute='metadata._deposit.cloned_from.value',
                              dump_only=True)


class DepositFormSchema(DepositSchema):
    """Schema for deposit v1 in JSON."""

    schemas = fields.Method('get_deposit_schemas', dump_only=True)
    webhooks = fields.Method('get_webhooks', dump_only=True)
    # workflows = fields.Method('get_workflows', dump_only=True)

    can_update = fields.Method('can_user_update', dump_only=True)
    can_admin = fields.Method('can_user_admin', dump_only=True)

    def get_webhooks(self, obj):
        webhooks = obj['deposit'].model.webhooks
        return GitWebhookSubscriberSchema(many=True).dump(webhooks).data

    # def get_workflows(self, obj):
    #     workflows = obj['deposit'].model.reana_workflows
    #     return ReanaWorkflowSchema(many=True).dump(workflows).data

    def get_deposit_schemas(self, obj):
        ui_schema = obj['deposit'].schema.deposit_options
        schema = current_jsonschemas.get_schema(
            obj['deposit'].schema.deposit_path,
            with_refs=True,
            resolved=True
        )
        return dict(schema=copy.deepcopy(schema), uiSchema=ui_schema)

    def can_user_update(self, obj):
        return UpdateDepositPermission(obj['deposit']).can()

    def can_user_admin(self, obj):
        return AdminDepositPermission(obj['deposit']).can()
