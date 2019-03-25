# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models
from odoo.addons.udes_stock.models import common
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _order = "requested_date asc, priority desc, id asc"

    # Add index to origin as this field is frequently used in searches
    origin = fields.Char(string='Source Document', 
                         help="Reference of the document that generated this sales order request.", 
                         index=True)

    # Rename states
    state = fields.Selection(selection_add=[
        ('sale', 'In Progress'),
        ('done', 'Done'),
    ])

    picking_ids = fields.One2many('stock.picking', inverse_name=None,
                                  compute="_compute_picking_ids_by_line")

    priority = fields.Selection(
        selection=common.PRIORITIES, inverse='_set_priority',
        default='1', string='Priority', index=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )

    @api.depends('order_line.move_ids.picking_id')
    def _compute_picking_ids_by_line(self):
        self.mapped('order_line.move_ids.picking_id')
        for order in self:
            order.picking_ids = order.mapped('order_line.move_ids.picking_id')

    @api.multi
    def _set_priority(self):
        for order in self:
            order.mapped('order_line.move_ids').write({
                'priority': order.priority
            })

    @api.model
    def get_available_stock_locations(self):
        """ Method returns stock locations that are considered (along with
         their children) stock available for fulfilling orders. Should be
        overridden where necessary """
        return self.env.ref('stock.stock_location_stock')

    @api.model
    def get_available_quantity(self, product, locations):
        """ Get available quantity of product_id within locations """
        Stock = self.env['stock.quant']
        domain = [('product_id', '=', product.id),
                  ('location_id', 'child_of', locations.ids)]
        quants = Stock.search(domain)
        available_quantity = sum(quants.mapped('quantity')) - \
                             sum(quants.mapped('reserved_quantity'))
        return available_quantity

    @api.model
    def cancel_orders_without_availability(self):
        """ From the current list of unconfirmed SO lines, cancel lines that
        cannot be fulfilled with current stock holding """
        OrderLine = self.env['sale.order.line']
        Order = self.env['sale.order']

        # Get order lines
        orders = Order.search([('state', 'in', ['sale', 'draft'])])

        # Get unreserved stock for each product in locations
        locations = self.get_available_stock_locations()
        stock = defaultdict(int)
        for product in orders.mapped('order_line.product_id'):
                stock[product] = stock[product] + \
                             self.get_available_quantity(product, locations)

        # Create empty record sets for SO lines
        can_fulfill = OrderLine.browse()
        cant_fulfill = OrderLine.browse()

        for r, batch in orders.batched(100):
            # Cache stuff
            batch.mapped('order_line')
            batch.mapped('order_line.move_ids')

            for order in batch:
                # Loop SO lines and deduct from stock dict, add order lines to
                # can or cant fulfill record sets
                for line in order.order_line.filtered(lambda x:
                                                      not x.is_cancelled):

                    # If any of the mls are done or assigned then skip this line
                    line_states = line.mapped('move_ids.state')
                    skip_states = ('assigned', 'done', 'cancel')
                    if any(x in line_states for x in skip_states):
                        continue

                    product = line.product_id
                    qty_ordered = line.product_uom_qty
                    if stock[product] >= qty_ordered:
                        can_fulfill |= line
                        stock[product] = stock[product]-qty_ordered
                    else:
                        cant_fulfill |= line

        if cant_fulfill:
            # Cancel these lines
            with self.statistics() as stats:
                cant_fulfill.action_cancel()
                cant_fulfill.write({'is_cancelled_due_shortage': True})

            _logger.info(
                "Sale lines on orders %s cancelled in %.2fs, %d queries, due to"
                " stock shortage,",
                ', '.join(cant_fulfill.mapped('order_id.name')),
                stats.elapsed,
                stats.count
            )

            cancelled_sales = cant_fulfill.mapped('order_id') \
                .filtered(lambda x: x.state == 'cancel')
            if cancelled_sales:
                _logger.info(
                    "Sales %s cancelling due to missing stock",
                    ', '.join(cancelled_sales.mapped('name'))
                )

        return cant_fulfill

    def check_delivered(self):
        """ Update sale orders state based on the states of their related
            pickings.
            An order is considered done or cancelled when all its pickings are
            done or cancelled respectively.
        """
        for order in self:
            done_pickings = order.picking_ids.filtered(
                    lambda ml: ml.state == 'done')
            cancel_pickings = order.picking_ids.filtered(
                    lambda ml: ml.state == 'cancel')
            if len(order.picking_ids) == len(done_pickings):
                order.action_done()
            if len(order.picking_ids) == len(cancel_pickings):
                order.with_context(from_sale=True).action_cancel()

    def action_cancel(self):
        """Override to cancel by moves instead of by pickings"""
        self.mapped('order_line').action_cancel()
        return self.write({'state': 'cancel'})

    def check_state_cancelled(self):
        to_cancel = self.browse()
        for order in self.filtered(
                lambda o: o.state not in ['done', 'cancel']):
            non_cancelled = order.order_line.filtered(
                lambda l: not l.is_cancelled)
            if len(non_cancelled) == 0:
                to_cancel |= order
        to_cancel.write({'state': 'cancel'})


class SaleOrderCancelWizard(models.TransientModel):
    """ This only exists to allow a confirm dialogue from a menu item """
    _name = "sale.order.cancel.wizard"
    result = fields.Char('Result')

    def cancel_unfulfillable_sales(self):
        with self.statistics() as stats:
            lines = self.env['sale.order'].cancel_orders_without_availability()

        if lines:
            message = "%s sale lines on %s orders cancelled in %.2fs" %\
                      (len(lines),
                       len(lines.mapped('order_id')),
                       stats.elapsed)
        else:
            message = "No orders cancelled"

        self.result = message
        template = self.env.ref('udes_sale_stock.view_cancellation_result')
        return {
            'name': 'Cancellation Result',
            'res_model': 'sale.order.cancel.wizard',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'view_id': template.id
        }
