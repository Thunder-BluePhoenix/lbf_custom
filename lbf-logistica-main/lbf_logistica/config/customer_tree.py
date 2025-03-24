from frappe import _

def get_data():
    return [
        {
            "label": _("Customer Tree"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Customer",
                    "label": _("Customer Tree"),
                    "route": "Tree/Customer",
                    "description": _("Tree view for Customers."),
                    "icon": "fa fa-sitemap",
                }
            ]
        }
    ]
