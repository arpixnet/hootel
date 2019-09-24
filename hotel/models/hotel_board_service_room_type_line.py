# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.addons import decimal_precision as dp

class HotelBoardServiceRoomTypeLine(models.Model):
    _name = 'hotel.board.service.room.type.line'
    _description = 'Services on Board Service included in Room'

    # Fields declaration
    hotel_board_service_room_type_id = fields.Many2one(
        'hotel.board.service.room.type',
        'Board Service Room',
        ondelete='cascade',
        required=True)
    product_id = fields.Many2one(
        'product.product',
        'Product',
        required=True,
        readonly=True)
    #TODO def default_amount "amount of service"
    amount = fields.Float('Amount', digits=dp.get_precision('Product Price'), default=0.0)
