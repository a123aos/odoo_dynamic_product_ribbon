from odoo import fields, models


STATUS_OPTIONS = [
    ("available", "Available"),
    ("pre_order", "Pre-order"),
    ("sold_out", "Sold Out"),
]


class ProductRibbon(models.Model):
    _inherit = "product.ribbon"

    assign = fields.Selection(
        selection_add=STATUS_OPTIONS,
        ondelete={
            "available": "cascade",
            "pre_order": "cascade",
            "sold_out": "cascade",
        },
    )

    def _is_applicable_for(self, product, price_data):
        self.ensure_one()

        if super()._is_applicable_for(product, price_data):
            return True

        if not product or product.type != "consu":
            return False

        website = self.env["website"].get_current_website()
        free_qty = website._get_product_available_qty(product.sudo())

        if self.assign == "available":
            return free_qty > 0

        if self.assign == "pre_order":
            return (
                free_qty <= 0
                and product.allow_out_of_stock_order
            )

        if self.assign == "sold_out":
            return (
                free_qty <= 0
                and not product.allow_out_of_stock_order
            )

        return False