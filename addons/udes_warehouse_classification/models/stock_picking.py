# -*- coding: utf-8 -*-

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_product_classfication_messages(self):
        """Find product classifications needed for a given picking"""
        return self.mapped("move_lines.product_id.u_product_warehouse_classification_ids").filtered(
            lambda c: self.picking_type_id in c.picking_type_ids
        ).mapped("alert_message")

    def _prepare_info(self, priorities=None, fields_to_fetch=None):
        """{doc}
           Extensions:
           - u_classification_messages: list
        """.format(doc=super()._prepare_info.__doc__)
        info = super()._prepare_info(priorities=priorities, fields_to_fetch=fields_to_fetch)
        if fields_to_fetch is None or "u_classification_messages" in fields_to_fetch:
            info["u_classification_messages"] = self._get_product_classfication_messages()
        return info
