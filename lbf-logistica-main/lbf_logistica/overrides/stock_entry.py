import frappe
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry


def update_serial_nos(doc, method):
    for item in doc.items:
        if item.custom_serial_noo and item.t_warehouse:
            # Fetch the custom_type_of_warehouse from the Warehouse document
            warehouse_doc = frappe.get_doc("Warehouse", item.t_warehouse)
            custom_type_of_warehouse = warehouse_doc.custom_type_of_warehouse
            
            # Update the Serial No document
            # serial_no_doc = frappe.get_doc("Serial No", item.custom_serial_noo)
            # serial_no_doc.warehouse = item.t_warehouse
            # serial_no_doc.custom_type_of_warehouse = custom_type_of_warehouse
            # serial_no_doc.save(ignore_permissions=True)
            frappe.db.set_value("Serial No", item.custom_serial_noo, "warehouse", item.t_warehouse) 
            frappe.db.set_value("Serial No", item.custom_serial_noo, "custom_type_of_warehouse", custom_type_of_warehouse) 

    # frappe.db.commit()  # Ensure all changes are saved






class CustomStockEntry(StockEntry):
    def validate_warehouse(self):
        pass

# # Hook to override the StockEntry class
# def override_stock_entry():
#     frappe.provide("custom_erpnext.overrides.stock_entry.CustomStockEntry")
#     StockEntry = CustomStockEntry

def validate_onsubmit(doc, method):
    for item in doc.items:
        if not item.t_warehouse:
            frappe.throw(f"Target warehouse is mandatory for row {item.idx}")
