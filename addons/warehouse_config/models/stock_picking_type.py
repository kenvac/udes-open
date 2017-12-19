# -*- coding: utf-8 -*-
from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    u_allow_swapping_packages = fields.Boolean('Allow swapping packages')
    u_skip_allowed = fields.Boolean(
            string='Skip allowed',
            default=False,
            help='Flag to indicate if the skip button will be shown.',
            )
    u_split_on_drop_off_picked = fields.Boolean('Split on drop off picked')
    u_suggest_qty = fields.Boolean(
        string='Suggest Qty',
        default=True,
        help='If True, suggest quantity on mobile if there is an expected quantity.',
    )
    u_over_receive = fields.Boolean(
        string='Over Receive',
        default=True,
        help='If True, allow additional items not in the ASN, or over the expected quantity, '
             'to be added at goods in.',
    )
    u_enforce_location_dest_id = fields.Boolean(
        string='Enforce Destination Location',
        default=False,
        help='Flag to indicate if the destination location of operations should '
             'be forced to be a child_of the picking location_dest_id.',)

    u_validate_real_time = fields.Boolean(
        string='Validate In Real Time',
        default=False,
        help='When True, operations are automatically validated in real time.'
    )
    u_target_storage_format = fields.Selection([
        ('pallet_products', 'Pallet of products'),
        ('pallet_packages', 'Pallet of packages'),
        ('package', 'Packages'),
        ('product', 'Products'),
    ],
        string='Target Storage Format',
    )
    u_user_scans = fields.Selection([
        ('pallet', 'Pallets'),
        ('package', 'Packages'),
        ('product', 'Products'),],
        string='What the User Scans',
        help='What the user scans when asked to '
        'scan something from pickings of this type')
