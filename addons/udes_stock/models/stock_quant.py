# -*- coding: utf-8 -*-

from odoo import models, _, api
from odoo.exceptions import ValidationError

from collections import defaultdict


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _get_removal_strategy_order(self, removal_strategy=None):
        """Change fifo removal strategy"""
        # NOTE: Preserve `NULLS FIRST` for `in_date` and use for `package_id` as well
        if removal_strategy == "fifo":
            return "in_date ASC NULLS FIRST, package_id ASC NULLS FIRST"
        return super(Quant, self)._get_removal_strategy_order(removal_strategy)

    def assert_not_reserved(self):
        """Ensure all quants in the recordset are unreserved."""
        reserved = self.filtered(lambda q: q.reserved_quantity > 0)
        if reserved:
            raise ValidationError(
                _(
                    "Items are reserved and cannot be moved. "
                    "Please speak to a team leader to resolve "
                    "the issue.\nAffected Items: %s"
                )
                % (
                    " ".join(reserved.mapped("package_id.name"))
                    if reserved.mapped("package_id")
                    else " ".join(reserved.mapped("product_id.display_name"))
                )
            )

    def assert_entire_packages(self):
        """Ensure the recordset self contains all the quants in package present
        in the recordset."""
        packages = self.mapped("package_id")
        package_quant_ids = packages._get_contained_quants()

        diff = package_quant_ids - self
        if diff:
            prob_packs = diff.mapped("package_id")
            raise ValidationError(
                _("Not all quants have been taken.\n" "Incomplete Packages:\n" "%s")
                % (" ".join(prob_packs.mapped("name")))
            )

    def assert_valid_location(self, location_id):
        """ Ensure the recorset self contains quants child of location_id
        """
        # TODO: check this function again, create generic is_valid/are_valid?
        Location = self.env["stock.location"]
        n_quant_locs = len(self.mapped("location_id"))
        child_locs = Location.search(
            [("id", "child_of", location_id), ("id", "in", self.mapped("location_id.id"))]
        )
        if len(child_locs) != n_quant_locs:
            raise ValidationError(
                _("The locations of some quants are not children of" " location %s")
                % Location.browse(location_id).name
            )

    def _gather(self, product_id, location_id, **kwargs):
        """ Call default _gather function, if quant_ids context variable
            is set the resulting quants are filtered by id.

            Context variable quant_ids might contain quants of different products.
        """
        quants = super(StockQuant, self)._gather(product_id, location_id, **kwargs)
        quant_ids = self.env.context.get("quant_ids")
        if quant_ids:
            quants = quants.filtered(lambda q: q.id in quant_ids)
        return quants

    def total_quantity(self):
        """ Returns the total quantity of the quants in self
        """
        return sum(self.mapped("quantity"))

    def group_quantity_by_product(self, only_available=False):
        """ Returns a dictionary with the total quantity per product,
            mapped by product_id.
        """
        products = defaultdict(int)
        for quant in self:
            value = quant.quantity
            if only_available:
                value -= quant.reserved_quantity
            products[quant.product_id.id] += value
        return products

    def _prepare_info(self):
        """
            Prepares the following info of the quant in self:
            - id: int
            - package_id: {stock.quant.package}
            - product_id: {product.product}
            - quantity: float
            - reserved_quantity: float
            - lot_id (optional): {stock.production.lot}
        """
        self.ensure_one()

        location_info = self.location_id.get_info()
        package_info = False
        if self.package_id:
            package_info = self.package_id.get_info()[0]

        res = {
            "id": self.id,
            "package_id": package_info,
            "product_id": self.product_id.get_info()[0],
            "location_id": location_info[0],
            "quantity": self.quantity,
            "reserved_quantity": self.reserved_quantity,
        }

        if self.lot_id:
            res["lot_id"] = self.lot_id.get_info()[0]

        return res

    def get_info(self):
        """ Return a list with the information of each quant in self.
        """
        res = []
        for quant in self:
            res.append(quant._prepare_info())

        return res

    @api.constrains("location_id")
    def quant_location_policy(self):
        self.ensure_one()
        self.location_id.apply_quant_policy()
