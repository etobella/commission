# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale_commission.tests import test_sale_commission
from odoo import fields
import dateutil.relativedelta


class TestSaleCommission(test_sale_commission.TestSaleCommission):

    def setUp(self):
        super(TestSaleCommission, self).setUp()
        self.agent_parent = self.env['res.partner'].create({
            'name': 'Parent',
            'supplier': True,
        })
        self.agent_1 = self.env['res.partner'].create({
            'name': 'Agent 1',
            'agent': True,
            'settlement': 'monthly',
            'lang': 'en_US',
            'agent_parent_id': self.agent_parent.id,
        })
        self.agent_2 = self.env['res.partner'].create({
            'name': 'Agent 2',
            'agent': True,
            'settlement': 'monthly',
            'lang': 'en_US',
            'agent_parent_id': self.agent_parent.id,
        })

    def test_multiagents(self):
        sale_orders = [self._create_sale_order(
            self.agent_1,
            self.commission_section_invoice
        ), self._create_sale_order(
            self.agent_2,
            self.commission_section_invoice
        )]
        for sale_order in sale_orders:
            sale_order.action_confirm()
            self.assertEqual(len(sale_order.invoice_ids), 0)
            payment = self.advance_inv_model.create({
                'advance_payment_method': 'all',
            })
            context = {"active_model": 'sale.order',
                       "active_ids": [sale_order.id],
                       "active_id": sale_order.id}
            payment.with_context(context).create_invoices()
            self.assertNotEqual(len(sale_order.invoice_ids), 0)
            for invoice in sale_order.invoice_ids:
                invoice.action_invoice_open()
                self.assertEqual(invoice.state, 'open')
            journals = self.env['account.journal'].search([
                ('type', '=', 'cash'),
                ('company_id', '=', sale_order.company_id.id)
            ], limit=1)
            for invoice in sale_order.invoice_ids:
                invoice.pay_and_reconcile(journals[:1], invoice.amount_total)
            self.assertTrue(sale_order.invoice_ids)
            self.assertEqual(sale_order.invoice_ids[:1].state, "paid")
        wizard = self.make_settle_model.create(
            {'date_to': (fields.Datetime.from_string(fields.Datetime.now()) +
                         dateutil.relativedelta.relativedelta(months=1))})
        wizard.action_settle()
        settlements = self.settle_model.search([('state', '=', 'settled')])
        self.assertNotEqual(len(settlements), 0)
        self.env['sale.commission.make.invoice'].with_context(
            settlement_ids=settlements.ids
        ).create({
            'journal': self.journal.id,
            'product': self.product.id,
            'date': fields.Datetime.now(),
        }).button_create()
        for settlement in settlements:
            self.assertEqual(settlement.state, 'invoiced')
        self.assertEqual(len(settlements), 2)
        self.assertEqual(
            self.agent_parent,
            settlements.mapped('invoice').mapped('partner_id'))
