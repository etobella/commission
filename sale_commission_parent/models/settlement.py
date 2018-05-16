# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, _


class Settlement(models.Model):
    _inherit = "sale.commission.settlement"

    def _prepare_invoice_header(self, settlement, journal, date=False):
        res = super()._prepare_invoice_header(settlement, journal, date)
        if settlement.agent.agent_parent_id:
            res['partner_id'] = settlement.agent.agent_parent_id
            invoice = self.env['account.invoice'].new(res)
            # Get other invoice values from partner onchange
            invoice._onchange_partner_id()
            res = invoice._convert_to_write(invoice._cache)
        return res

    def create_invoice_header(self, journal, date):
        """Hook that can be used in order to group invoices or
        find open invoices
        """
        inv_type = 'in_invoice' if journal.type == 'purchase' else 'in_refund'
        partner = self.agent.agent_parent_id
        if not partner:
            partner = self.agent
        invoice = self.env['account.invoice'].search([
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', partner.id),
            ('type', '=', inv_type),
            ('journal_id', '=', journal.id),
            ('state', '=', 'draft')
        ], limit=1)
        if invoice:
            return invoice
        return super().create_invoice_header(journal, date)

    def _prepare_invoice_line(self, settlement, invoice, product):
        res = super()._prepare_invoice_line(settlement, invoice, product)
        if settlement.agent.agent_parent_id:
            res['name'] += "\n" + _('Agent: %s') % settlement.agent.name
        return res

