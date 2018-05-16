# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    agent_parent_id = fields.Many2one(
        comodel_name="res.partner",
        domain="[('supplier', '=', True)]")
