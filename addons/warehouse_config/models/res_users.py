# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.errors import ValidationError

class ResUser(models.Model):

    _inherit = 'res.users'

    @api.model
    def get_user_warehouse(self):
        """ Get the warehouse of the user by chain of the company
        """
        Warehouse = self.env['stock.warehouse']
        user = self.search([('id', '=', self.env.uid)])
        if not user:
            raise ValidationError(_('Cannot find user to get warehouse.'))
        warehouse = Warehouse.search([('company_id', '=', user.company_id.id)])
        if not warehouse:
            raise ValidationError(_('Cannot find a warehouse for user'))
        if len(warehouse) > 1:
            raise ValidationError(_('Found multiple warehouses for user'))

        return warehouse
