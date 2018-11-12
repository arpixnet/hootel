# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class HotelRoomImporter(Component):
    _name = 'node.room.importer'
    _inherit = 'node.importer'
    _apply_on = ['node.room']
    _usage = 'node.room.importer'

    @api.model
    def fetch_rooms(self):
        results = self.backend_adapter.fetch_rooms()
        room_mapper = self.component(usage='import.mapper',
                                     model_name='node.room')

        node_room_obj = self.env['node.room']
        for rec in results:
            map_record = room_mapper.map_record(rec)
            room = node_room_obj.search([('external_id', '=', rec['id'])],
                                        limit=1)
            # NEED REVIEW Import a record triggers a room.write / room.create back to the node
            if room:
                room.write(map_record.values())
            else:
                room.create(map_record.values(for_create=True))


class NodeRoomImportMapper(Component):
    _name = 'node.room.import.mapper'
    _inherit = 'node.import.mapper'
    _apply_on = 'node.room'

    # SEE m2o_to_external at https://github.com/OCA/connector/blob/11.0/connector/components/mapper.py#L146

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
        ('capacity', 'capacity'),
        ('room_type_id', 'room_type_id'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
