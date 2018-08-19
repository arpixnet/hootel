# -*- coding: utf-8 -*-
# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import time
import pytz
import logging
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm, UserError, ValidationError
from odoo.tools import (
    misc,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo import models, fields, api, _
from odoo.addons.hotel import date_utils
_logger = logging.getLogger(__name__)

from odoo.addons import decimal_precision as dp


class HotelFolio(models.Model):

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        args += ([('name', operator, name)])
        mids = self.search(args, limit=100)
        return mids.name_get()

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state folio on the menu badge.
         @param self: object pointer
        """
        return self.search_count([('state', '=', 'draft')])

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(HotelFolio, self).copy(default=default)

    @api.multi
    def _invoiced(self, name, arg):
        '''
        @param self: object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        pass
        # return self.env['sale.order']._invoiced(name, arg)

    @api.multi
    def _invoiced_search(self, obj, name, args):
        '''
        @param self: object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        pass
        # return self.env['sale.order']._invoiced_search(obj, name, args)

    # @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        pass
    # @api.depends('product_id.invoice_policy', 'order_id.state')
    def _compute_qty_delivered_updateable(self):
        pass
    # @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        pass
    # @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        pass
    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        pass
    # @api.depends('order_line.price_total')
    def _amount_all(self):
        pass

    _name = 'hotel.folio'
    _description = 'Hotel Folio'

    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Folio Number', readonly=True, index=True,
                       default='New')
    partner_id = fields.Many2one('res.partner',
                                 track_visibility='onchange')
    # partner_invoice_id = fields.Many2one('res.partner',
    #                                      string='Invoice Address',
    #                                      readonly=True, required=True,
    #                                      states={'draft': [('readonly', False)],
    #                                              'sent': [('readonly', False)]},
    #                                      help="Invoice address for current sales order.")

    # For being used directly in the Folio views
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    phone = fields.Char('Phone', related='partner_id.phone')

    state = fields.Selection([('draft', 'Pre-reservation'), ('confirm', 'Pending Entry'),
                              ('booking', 'On Board'), ('done', 'Out'),
                              ('cancelled', 'Cancelled')],
                             'State', readonly=True,
                             default=lambda *a: 'draft',
                             track_visibility='onchange')

    room_lines = fields.One2many('hotel.reservation', 'folio_id',
                                 readonly=False,
                                 states={'done': [('readonly', True)]},
                                 help="Hotel room reservation detail.",)

    service_line_ids = fields.One2many('hotel.service', 'folio_id',
                                  readonly=False,
                                  states={'done': [('readonly', True)]},
                                  help="Hotel services detail provide to "
                                       "customer and it will include in "
                                       "main Invoice.")
    # service_line_ids = fields.One2many('hotel.service.line', 'folio_id',
    #                                    readonly=False,
    #                                    states={'done': [('readonly', True)]},
    #                                    help="Hotel services detail provide to"
    #                                         "customer and it will include in "
    #                                         "main Invoice.")
    # has no sense used as this way
    hotel_invoice_id = fields.Many2one('account.invoice', 'Invoice')

    company_id = fields.Many2one('res.company', 'Company')

    # currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id',
    #                               string='Currency', readonly=True, required=True)

    # pricelist_id = fields.Many2one('product.pricelist',
    #                                string='Pricelist',
    #                                required=True,
    #                                readonly=True,
    #                                states={'draft': [('readonly', False)],
    #                                        'sent': [('readonly', False)]},
    #                                help="Pricelist for current sales order.")
    # Monetary to Float
    invoices_amount = fields.Float(compute='compute_invoices_amount',
                                   store=True,
                                   string="Pending in Folio")
    # Monetary to Float
    refund_amount = fields.Float(compute='compute_invoices_amount',
                                    store=True,
                                    string="Payment Returns")
    # Monetary to Float
    invoices_paid = fields.Float(compute='compute_invoices_amount',
                                 store=True, track_visibility='onchange',
                                 string="Payments")

    booking_pending = fields.Integer('Booking pending',
                                     compute='_compute_cardex_count')
    cardex_count = fields.Integer('Cardex counter',
                                  compute='_compute_cardex_count')
    cardex_pending = fields.Boolean('Cardex Pending',
                                    compute='_compute_cardex_count')
    cardex_pending_num = fields.Integer('Cardex Pending',
                                        compute='_compute_cardex_count')
    checkins_reservations = fields.Integer('checkins reservations')
    checkouts_reservations = fields.Integer('checkouts reservations')
    partner_internal_comment = fields.Text(string='Internal Partner Notes',
                                           related='partner_id.comment')
    internal_comment = fields.Text(string='Internal Folio Notes')
    cancelled_reason = fields.Text('Cause of cancelled')
    payment_ids = fields.One2many('account.payment', 'folio_id',
                                  readonly=True)
    return_ids = fields.One2many('payment.return', 'folio_id',
                                 readonly=True)
    prepaid_warning_days = fields.Integer(
        'Prepaid Warning Days',
        help='Margin in days to create a notice if a payment \
                advance has not been recorded')
    reservation_type = fields.Selection([('normal', 'Normal'),
                                         ('staff', 'Staff'),
                                         ('out', 'Out of Service')],
                                        'Type', default=lambda *a: 'normal')
    channel_type = fields.Selection([('door', 'Door'),
                                     ('mail', 'Mail'),
                                     ('phone', 'Phone'),
                                     ('web', 'Web')], 'Sales Channel', default='door')
    num_invoices = fields.Integer(compute='_compute_num_invoices')
    rooms_char = fields.Char('Rooms', compute='_computed_rooms_char')
    segmentation_ids = fields.Many2many('res.partner.category',
                                        string='Segmentation')
    has_confirmed_reservations_to_send = fields.Boolean(
        compute='_compute_has_confirmed_reservations_to_send')
    has_cancelled_reservations_to_send = fields.Boolean(
        compute='_compute_has_cancelled_reservations_to_send')
    has_checkout_to_send = fields.Boolean(
        compute='_compute_has_checkout_to_send')
    # fix_price = fields.Boolean(compute='_compute_fix_price')
    date_order = fields.Datetime(
        string='Order Date',
        required=True, readonly=True, index=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        copy=False, default=fields.Datetime.now)

    invoice_ids = fields.Many2many('account.invoice', string='Invoices',
                                   compute='_get_invoiced', readonly=True, copy=False)
    invoice_status = fields.Selection([('upselling', 'Upselling Opportunity'),
                                       ('invoiced', 'Fully Invoiced'),
                                       ('to invoice', 'To Invoice'),
                                       ('no', 'Nothing to Invoice')],
                                      string='Invoice Status',
                                      compute='_compute_invoice_status',
                                      store=True, readonly=True, default='no')
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    note = fields.Text('Terms and conditions')
    # layout_category_id = fields.Many2one('sale.layout_category', string='Section')

    user_id = fields.Many2one('res.users', string='Salesperson', index=True,
                              track_visibility='onchange', default=lambda self: self.env.user)

    sequence = fields.Integer(string='Sequence', default=10)
    # sale.order
    amount_total = fields.Float(string='Total', store=True, readonly=True,
                                   track_visibility='always')


    def _compute_fix_price(self):
        for record in self:
            for res in record.room_lines:
                if res.fix_total == True:
                    record.fix_price = True
                    break
                else:
                    record.fix_price = False

    def action_recalcule_payment(self):
        for record in self:
            for res in record.room_lines:
                res.on_change_checkin_checkout_product_id()

    def _computed_rooms_char(self):
        for record in self:
            rooms = ', '.join(record.mapped('room_lines.room_id.name'))
            record.rooms_char = rooms

    @api.model
    def recompute_amount(self):
        folios = self.env['hotel.folio']
        if folios:
            folios = folios.filtered(lambda x: (
                x.name == folio_name))
        folios.compute_invoices_amount()

    @api.multi
    def _compute_num_invoices(self):
        pass
        # for fol in self:
        #     fol.num_invoices =  len(self.mapped('invoice_ids.id'))

    @api.model
    def daily_plan(self):
        _logger.info('daily_plan')
        self._cr.execute("update hotel_folio set checkins_reservations = 0, \
            checkouts_reservations = 0 where checkins_reservations > 0  \
            or checkouts_reservations > 0")
        folios_in = self.env['hotel.folio'].search([
            ('room_lines.is_checkin', '=', True)
        ])
        folios_out = self.env['hotel.folio'].search([
            ('room_lines.is_checkout', '=', True)
        ])
        for fol in folios_in:
            count_checkin = fol.room_lines.search_count([
                ('is_checkin', '=', True), ('folio_id.id', '=', fol.id)
            ])
            fol.write({'checkins_reservations': count_checkin})
        for fol in folios_out:
            count_checkout = fol.room_lines.search_count([
                ('is_checkout', '=', True),
                ('folio_id.id', '=', fol.id)
            ])
            fol.write({'checkouts_reservations': count_checkout})
        return True

    # @api.depends('order_line.price_total', 'payment_ids', 'return_ids')
    @api.multi
    def compute_invoices_amount(self):
        _logger.info('compute_invoices_amount')

    @api.multi
    def action_pay(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = self.invoices_amount
        view_id = self.env.ref('hotel.view_account_payment_folio_form').id
        return{
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'context': {
                'default_folio_id': self.id,
                'default_amount': amount,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': partner,
                'default_communication': self.name,
            },
            'target': 'new',
        }

    @api.multi
    def action_payments(self):
        self.ensure_one()
        payments_obj = self.env['account.payment']
        payments = payments_obj.search([('folio_id','=',self.id)])
        payment_ids = payments.mapped('id')
        invoices = self.mapped('invoice_ids.id')
        return{
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', payment_ids)],
        }

    @api.multi
    def open_invoices_folio(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_return_payments(self):
        self.ensure_one()
        return_move_ids = []
        acc_pay_obj = self.env['account.payment']
        payments = acc_pay_obj.search([
                '|',
                ('invoice_ids', 'in', self.invoice_ids.ids),
                ('folio_id', '=', self.id)
            ])
        return_move_ids += self.invoice_ids.filtered(
            lambda invoice: invoice.type == 'out_refund').mapped(
            'payment_move_line_ids.move_id.id')
        return_lines = self.env['payment.return.line'].search([(
            'move_line_ids','in',payments.mapped(
            'move_line_ids.id'))])
        return_move_ids += return_lines.mapped('return_id.move_id.id')

        return{
            'name': _('Returns'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_move_ids)],
        }

    @api.multi
    def action_checks(self):
        self.ensure_one()
        rooms = self.mapped('room_lines.id')
        return {
            'name': _('Cardexs'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'cardex',
            'type': 'ir.actions.act_window',
            'domain': [('reservation_id', 'in', rooms)],
            'target': 'new',
        }

    @api.multi
    def action_folios_amount(self):
        now_utc_dt = date_utils.now()
        now_utc_str = now_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        reservations = self.env['hotel.reservation'].search([
            ('checkout', '<=', now_utc_str)
        ])
        folio_ids = reservations.mapped('folio_id.id')
        folios = self.env['hotel.folio'].search([('id', 'in', folio_ids)])
        folios = folios.filtered(lambda r: r.invoices_amount > 0)
        return {
            'name': _('Pending'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.folio',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', folios.ids)]
        }

    @api.depends('room_lines')
    def _compute_has_confirmed_reservations_to_send(self):
        has_to_send = False
        for rline in self.room_lines:
            if rline.splitted:
                master_reservation = rline.parent_reservation or rline
                has_to_send = self.env['hotel.reservation'].search_count([
                    ('splitted', '=', True),
                    ('folio_id', '=', self.id),
                    ('to_send', '=', True),
                    ('state', 'in', ('confirm', 'booking')),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
                    ('id', '=', master_reservation.id),
                ]) > 0
            elif rline.to_send and rline.state in ('confirm', 'booking'):
                has_to_send = True
                break
        self.has_confirmed_reservations_to_send = has_to_send

    @api.depends('room_lines')
    def _compute_has_cancelled_reservations_to_send(self):
        has_to_send = False
        for rline in self.room_lines:
            if rline.splitted:
                master_reservation = rline.parent_reservation or rline
                has_to_send = self.env['hotel.reservation'].search_count([
                    ('splitted', '=', True),
                    ('folio_id', '=', self.id),
                    ('to_send', '=', True),
                    ('state', '=', 'cancelled'),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
                    ('id', '=', master_reservation.id),
                ]) > 0
            elif rline.to_send and rline.state == 'cancelled':
                has_to_send = True
                break
        self.has_cancelled_reservations_to_send = has_to_send

    @api.depends('room_lines')
    def _compute_has_checkout_to_send(self):
        has_to_send = True
        for rline in self.room_lines:
            if rline.splitted:
                master_reservation = rline.parent_reservation or rline
                nreservs = self.env['hotel.reservation'].search_count([
                    ('splitted', '=', True),
                    ('folio_id', '=', self.id),
                    ('to_send', '=', True),
                    ('state', '=', 'done'),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
                    ('id', '=', master_reservation.id),
                ])
                if nreservs != len(self.room_lines):
                    has_to_send = False
            elif not rline.to_send or rline.state != 'done':
                has_to_send = False
                break
        self.has_checkout_to_send = has_to_send

    @api.multi
    def _compute_cardex_count(self):
        _logger.info('_compute_cardex_amount')
        for fol in self:
            num_cardex = 0
            pending = False
            if fol.reservation_type == 'normal':
                for reser in fol.room_lines:
                    if reser.state != 'cancelled' and \
                            not reser.parent_reservation:
                        num_cardex += len(reser.cardex_ids)
                fol.cardex_count = num_cardex
                pending = 0
                for reser in fol.room_lines:
                    if reser.state != 'cancelled' and \
                            not reser.parent_reservation:
                        pending += (reser.adults + reser.children) \
                                          - len(reser.cardex_ids)
                if pending <= 0:
                    fol.cardex_pending = False
                else:
                    fol.cardex_pending = True
        fol.cardex_pending_num = pending

    @api.multi
    def go_to_currency_exchange(self):
        '''
         when Money Exchange button is clicked then this method is called.
        -------------------------------------------------------------------
        @param self: object pointer
        '''
        _logger.info('go_to_currency_exchange')
        pass
        # cr, uid, context = self.env.args
        # context = dict(context)
        # for rec in self:
        #     if rec.partner_id.id and len(rec.room_lines) != 0:
        #         context.update({'folioid': rec.id, 'guest': rec.partner_id.id,
        #                         'room_no': rec.room_lines[0].product_id.name})
        #         self.env.args = cr, uid, misc.frozendict(context)
        #     else:
        #         raise except_orm(_('Warning'), _('Please Reserve Any Room.'))
        # return {'name': _('Currency Exchange'),
        #         'res_model': 'currency.exchange',
        #         'type': 'ir.actions.act_window',
        #         'view_id': False,
        #         'view_mode': 'form,tree',
        #         'view_type': 'form',
        #         'context': {'default_folio_no': context.get('folioid'),
        #                     'default_hotel_id': context.get('hotel'),
        #                     'default_guest_name': context.get('guest'),
        #                     'default_room_number': context.get('room_no')
        #                     },
        #         }

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio.
        """
        _logger.info('create')
        if not 'service_line_ids' and 'folio_id' in vals:
            tmp_room_lines = vals.get('room_lines', [])
            vals['order_policy'] = vals.get('hotel_policy', 'manual')
            vals.update({'room_lines': []})
            for line in (tmp_room_lines):
                line[2].update({'folio_id': folio_id})
            vals.update({'room_lines': tmp_room_lines})
            folio_id = super(HotelFolio, self).create(vals)
        else:
            if not vals:
                vals = {}
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.folio')
            folio_id = super(HotelFolio, self).create(vals)

        return folio_id

    @api.multi
    def write(self, vals):
        if 'room_lines' in vals and vals['room_lines'][0][2] and 'reservation_line_ids' in vals['room_lines'][0][2] and vals['room_lines'][0][2]['reservation_line_ids'][0][0] == 5:
            del vals['room_lines']
        return super(HotelFolio, self).write(vals)

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        '''
        _logger.info('onchange_partner_id')
        pass
        # self.update({
        #     'currency_id': self.env.ref('base.main_company').currency_id,
        #     'partner_invoice_id': self.partner_id and self.partner_id.id or False,
        #     'partner_shipping_id': self.partner_id and self.partner_id.id or False,
        #     'pricelist_id': self.partner_id and self.partner_id.property_product_pricelist.id or False,
        # })
        # """
        # Warning messajes saved in partner form to folios
        # """
        # if not self.partner_id:
        #     return
        # warning = {}
        # title = False
        # message = False
        # partner = self.partner_id
        #
        # # If partner has no warning, check its company
        # if partner.sale_warn == 'no-message' and partner.parent_id:
        #     partner = partner.parent_id
        #
        # if partner.sale_warn != 'no-message':
        #     # Block if partner only has warning but parent company is blocked
        #     if partner.sale_warn != 'block' and partner.parent_id \
        #             and partner.parent_id.sale_warn == 'block':
        #         partner = partner.parent_id
        #     title = _("Warning for %s") % partner.name
        #     message = partner.sale_warn_msg
        #     warning = {
        #             'title': title,
        #             'message': message,
        #     }
        #     if self.partner_id.sale_warn == 'block':
        #         self.update({
        #             'partner_id': False,
        #             'partner_invoice_id': False,
        #             'partner_shipping_id': False,
        #             'pricelist_id': False
        #         })
        #         return {'warning': warning}
        #
        # if warning:
        #     return {'warning': warning}

    @api.multi
    def button_dummy(self):
        '''
        @param self: object pointer
        '''
        # for folio in self:
        #     folio.order_id.button_dummy()
        return True

    @api.multi
    def action_done(self):
        for line in self.room_lines:
            if line.state == "booking":
                line.action_reservation_checkout()

    @api.multi
    def action_invoice_create(self, grouped=False, states=None):
        '''
        @param self: object pointer
        '''
        pass
        # if states is None:
        #     states = ['confirmed', 'done']
        # order_ids = [folio.order_id.id for folio in self]
        # sale_obj = self.env['sale.order'].browse(order_ids)
        # invoice_id = (sale_obj.action_invoice_create(grouped=False,
        #                                              states=['confirmed',
        #                                                      'done']))
        # for line in self:
        #     values = {'invoiced': True,
        #               'state': 'progress' if grouped else 'progress',
        #               'hotel_invoice_id': invoice_id
        #               }
        #     line.write(values)
        # return invoice_id

    @api.multi
    def advance_invoice(self):
        pass
        # order_ids = [folio.order_id.id for folio in self]
        # sale_obj = self.env['sale.order'].browse(order_ids)
        # invoices = action_invoice_create(self, grouped=True)
        # return invoices

    @api.multi
    def action_cancel(self):
        '''
        @param self: object pointer
        '''
        pass
        # for sale in self:
        #     if not sale.order_id:
        #         raise ValidationError(_('Order id is not available'))
        #     for invoice in sale.invoice_ids:
        #         invoice.state = 'cancel'
        #     sale.room_lines.action_cancel()
        #     sale.order_id.action_cancel()


    @api.multi
    def action_confirm(self):
        _logger.info('action_confirm')

    @api.multi
    def print_quotation(self):
        pass
        # self.order_id.filtered(lambda s: s.state == 'draft').write({
        #     'state': 'sent',
        # })
        # return self.env.ref('sale.report_saleorder').report_action(self, data=data)

    @api.multi
    def action_cancel_draft(self):
        _logger.info('action_confirm')

    @api.multi
    def send_reservation_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel',
                            'mail_template_hotel_reservation')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.folio',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.multi
    def send_exit_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel',
                            'mail_template_hotel_exit')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }


    @api.multi
    def send_cancel_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel',
                            'mail_template_hotel_cancel')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_str = time.strftime(dt)
        now_date = datetime.strptime(now_str, dt)
        ir_model_data = self.env['ir.model.data']
        template_id = (ir_model_data.get_object_reference
                       ('hotel_reservation',
                        'mail_template_reservation_reminder_24hrs')[1])
        template_rec = self.env['mail.template'].browse(template_id)
        for reserv_rec in self.search([]):
            checkin_date = (datetime.strptime(reserv_rec.checkin, dt))
            difference = relativedelta(now_date, checkin_date)
            if(difference.days == -1 and reserv_rec.partner_id.email and
               reserv_rec.state == 'confirm'):
                template_rec.send_mail(reserv_rec.id, force_send=True)
        return True

    @api.multi
    def unlink(self):
        # for record in self:
        #     record.order_id.unlink()
        return super(HotelFolio, self).unlink()

    @api.multi
    def get_grouped_reservations_json(self, state, import_all=False):
        self.ensure_one()
        info_grouped = []
        for rline in self.room_lines:
            if (import_all or rline.to_send) and not rline.parent_reservation and rline.state == state:
                dates = rline.get_real_checkin_checkout()
                vals = {
                    'num': len(
                        self.room_lines.filtered(lambda r: r.get_real_checkin_checkout()[0] == dates[0] and r.get_real_checkin_checkout()[1] == dates[1] and r.room_type_id.id == rline.room_type_id.id and (r.to_send or import_all) and not r.parent_reservation and r.state == rline.state)
                    ),
                    'room_type': {
                        'id': rline.room_type_id.id,
                        'name': rline.room_type_id.name,
                    },
                    'checkin': dates[0],
                    'checkout': dates[1],
                    'nights': len(rline.reservation_line_ids),
                    'adults': rline.adults,
                    'childrens': rline.children,
                }
                founded = False
                for srline in info_grouped:
                    if srline['num'] == vals['num'] and srline['room_type']['id'] == vals['room_type']['id'] and srline['checkin'] == vals['checkin'] and srline['checkout'] == vals['checkout']:
                        founded = True
                        break
                if not founded:
                    info_grouped.append(vals)
        return sorted(sorted(info_grouped, key=lambda k: k['num'], reverse=True), key=lambda k: k['room_type']['id'])