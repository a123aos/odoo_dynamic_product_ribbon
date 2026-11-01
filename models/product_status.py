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

SCHEMA_AVAILABILITY = {
    "available": "https://schema.org/InStock",
    "pre_order": "https://schema.org/PreOrder",
    "sold_out": "https://schema.org/OutOfStock",
}


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _to_markup_data(self, website):
        """Keep Product JSON-LD availability in sync with the displayed ribbon."""
        self.ensure_one()
        markup_data = super()._to_markup_data(website)

        # Use the same ribbon resolution as the website product page:
        # variant ribbon, template ribbon, then automatically assigned ribbon.
        ribbon = self.product_tmpl_id._get_ribbon(variant=self)
        offers = markup_data.get("offers")
        if not isinstance(offers, dict):
            return markup_data

        # A manually assigned "Coming Soon" ribbon means the product is not
        # open for ordering yet. Do not claim that it is in stock or available
        # for pre-order in structured data.
        ribbon_name = (ribbon.name or "").strip().casefold().replace("-", " ").replace("_", " ")
        if ribbon.assign == "manual" and ribbon_name == "coming soon":
            offers.pop("availability", None)
            return markup_data

        availability = SCHEMA_AVAILABILITY.get(ribbon.assign)
        if availability:
            offers["availability"] = availability

        return markup_data

