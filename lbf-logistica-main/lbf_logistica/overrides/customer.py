import frappe
from frappe import _

@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False):
    """
    Fetch child nodes for the tree view
    """
    filters = []
    if parent:
        filters.append(["custom_parent_customer", "=", parent])
    else:
        filters.append(["custom_parent_customer", "is", "not set"])
    
    customers = frappe.get_list(
        "Customer",
        fields=["name as value", "custom_is_parent as expandable"],
        filters=filters,
        order_by="name asc"
    )
    return customers



# @frappe.whitelist()
# def validate_default_supplier(doc, method):
#     # Count the number of rows where is_default is checked
#     default_suppliers = [row for row in doc.custom_suppliers if row.is_default]

#     if default_suppliers:

#         if len(default_suppliers) > 1:
#             frappe.throw("Only one supplier can be marked as Default in the Suppliers table.")
#         elif len(default_suppliers) < 1:
#             frappe.throw("Please mark one supplier as Default in the Suppliers table.")


@frappe.whitelist()
def validate_default_supplier_address(doc, method):
    # Count the number of rows where is_default is checked
    default_suppliers = [row for row in doc.custom_transporters if row.is_default]

    if default_suppliers:

        if len(default_suppliers) > 1:
            frappe.throw("Only one supplier can be marked as Default in the Suppliers table.")
        elif len(default_suppliers) < 1:
            frappe.throw("Please mark one supplier as Default in the Suppliers table.")


