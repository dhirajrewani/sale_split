{
    "name": "Sale Quantity Order Split",
    "version": "1.0",
    "category": "Sales",
    "summary": "Limit the quantity of a product per sale order and split the excess onto new orders",
    "description": """
        Adds a "Max Qty per Order" (qty_order_split) field on products. Sale orders
        containing a line above that limit cannot be confirmed. An OWL widget on the
        order lines warns the user and offers a one-click split onto new order(s).
    """,
    "depends": ["sale_management"],
    "data": [
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_qty_split/static/src/qty_split/*",
        ],
    },
    "license": "LGPL-3",
    "application": False,
    "installable": True,
}
