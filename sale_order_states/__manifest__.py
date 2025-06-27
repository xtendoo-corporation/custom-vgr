{
    "name": "VGR SALES ORDER STATES",
    "version": "17.0.1.0.1",
    "category": "Custom Sales Order States",
    "author": "Xtendoo",
    "license": "AGPL-3",
    "depends": [
        "base",
        "web",
        "sale",
        "sale_order_type",
        "mail",
    ],
    "data": [
        "views/sale_order_state_views.xml",
        "views/sale_order_form.xml",
        "security/ir.model.access.csv",
        "data/states_sequence.xml",
        "views/mail_activitys.xml",
    ],
    "installable": True,
}
