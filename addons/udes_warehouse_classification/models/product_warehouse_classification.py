# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductWarehouseClassification(models.Model):
    _name = "product.warehouse.classification"
    _description = "Information used for messaging about product qualities."
    _order = "sequence, name"

    name = fields.Char(string="Name for classification")
    alert_message = fields.Char(
        string="Alert message", help="Message to be displayed when alerting.",
    )
    label_message = fields.Char(
        string="Label message", help="Message to be displayed when attaching to label.",
    )
    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type",
        string="picking_type_ids",
        help="Picking types which are concerned with classification",
    )
    report_template_ids = fields.Many2many(
        comodel_name="ir.actions.report",
        string="report_template_ids",
        help="Record templates for which the label message should be included when printing.",
    )
    sequence = fields.Integer(
        string="Sequence", default=1, help="Allows for ordering classifications."
    )
    show_when = fields.Char(help="A string to dictate at which actions/events the message is shown.")
