import frappe
from frappe.model.document import Document
from frappe import _

from frappe.utils import flt, now_datetime, now

import json


# def before_save(doc, method=None):
#     # Check if custom item code and quantity are provided
#     if doc.custom_item_code and doc.custom_item_qty:
#         # Ensure locations child table exists
#         if not doc.locations:
#             doc.locations = []

#         # Add entry to locations child table
#         doc.append("locations", {
#             "doctype": "Pick List Item",  # Ensure this matches the child doctype
#             "item_code": doc.custom_item_code,
#             "qty": doc.custom_item_qty,
#             # "warehouse": ""  # Set a default or fetch warehouse dynamically if needed
#         })

#         # Log the operation for debugging purposes
#         frappe.log_error(
#             title="Pick List Locations Populated",
#             message=f"Added item_code: {doc.custom_item_code}, qty: {doc.custom_item_qty} to locations."
#         )


@frappe.whitelist()
def create_stock_entry(pick_list_name, dialog_data=None):
    
    pick_list = frappe.get_doc("Pick List", pick_list_name)
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = pick_list.company
    stock_entry.purpose = pick_list.purpose

    if dialog_data:
        dialog_data = json.loads(dialog_data)  # Convert dialog data to a Python list

    for item in pick_list.custom_item_locations:
        # Find the corresponding item in dialog_data to get updated target_warehouse
        if dialog_data:
            dialog_item = next((d for d in dialog_data if d.get("idx") == item.idx), {})
            target_warehouse = dialog_item.get("target_warehouse", item.target_warehouse)
        else:
            target_warehouse = item.target_warehouse

        serial_numbers = item.serial_no.split('\n') if item.serial_no else []
        item_details = frappe.get_doc("Item", item.item_code)
        item_uom = item_details.uoms[0].uom if item_details.uoms else None

        for serial_no in serial_numbers:
            serial_doc = frappe.get_doc("Serial No", serial_no)
            custom_barcode = serial_doc.custom_barcode if hasattr(serial_doc, "custom_barcode") else None
            stock_entry.append("items", {
                "item_code": item.item_code,
                "qty": 1,
                "s_warehouse": item.location,
                "t_warehouse": target_warehouse,  # Use the updated target warehouse from the dialog
                "custom_serial_noo": serial_no,
                "custom_batch_id": item.batch_no,
                "uom": item_uom,
                # "stock_uom": item.stock_uom,
                # "conversion_factor": item.conversion_factor,
                # "description": item.description if hasattr(item, "description") else None,
                "custom_barcode_of_serial": custom_barcode
            })

    stock_entry.flags.ignore_permissions = True
    stock_entry.flags.ignore_validate = True
    stock_entry.flags.ignore_mandatory = True
    stock_entry.insert(ignore_permissions=True)
    stock_entry.run_method('validate')
    stock_entry.submit()

    pick_list.db_set("custom_pl_status", "Completed")
    return stock_entry.name


@frappe.whitelist()
def create_stock_entries(pick_list_id, items):
    items = frappe.parse_json(items)
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = frappe.db.get_value("Pick List", pick_list_id, "company")
    stock_entry.purpose = frappe.db.get_value("Pick List", pick_list_id, "purpose") 

    for item in items:
        serial_numbers = item.get("serial_no", "").split("\n")
        if serial_numbers:
            for serial_no in serial_numbers:
                if serial_no.strip():  
                    custom_barcode = frappe.db.get_value("Serial No", serial_no.strip(), "custom_barcode")
                    stock_entry.append("items", {
                        "item_code": item.get("item_code"),
                        "qty": 1, 
                        "s_warehouse": item.get("source_warehouse"),
                        "t_warehouse": item.get("target_warehouse"),
                        "uom": item.get("uom"),
                        "stock_uom": item.get("uom"),
                        "custom_batch_id": item.get("batch_no"),
                        "custom_serial_noo": serial_no.strip(),  
                        "description": item.get("description", None),
                        "custom_barcode_of_serial": custom_barcode,
                    })
        else:
            stock_entry.append("items", {
                "item_code": item.get("item_code"),
                "qty": item.get("qty"),
                "s_warehouse": item.get("source_warehouse"),
                "t_warehouse": item.get("target_warehouse"),
                "uom": item.get("uom"),
                "stock_uom": item.get("uom"),
                "custom_batch_id": item.get("batch_no"),
                "description": item.get("description", None)
            })

    stock_entry.flags.ignore_permissions = True
    stock_entry.flags.ignore_validate = True
    stock_entry.flags.ignore_mandatory = True
    stock_entry.insert(ignore_permissions=True)
    stock_entry.run_method('validate')  
    stock_entry.submit()
    frappe.db.set_value("Pick List", pick_list_id, "custom_pl_status", "Completed")  

    return stock_entry.name





def status_change_on_submit(doc, method=None):
    doc.custom_pl_status = "In Progress"
    doc.custom_submission_datetime = now_datetime()
    doc.custom_submission_date = now()
    doc.db_update()
def status_change_on_cancel(doc, method=None):
    doc.custom_pl_status = "Cancelled"
    doc.db_update()
    


def validate_submit(doc, method=None):
    selected_qty = doc.custom_total_qty_selected
    required_qty = doc.custom_item_qty

    if selected_qty != required_qty:
        frappe.throw(
                    f"The selected Qty ({selected_qty}) Does not Match With Required Qty ({required_qty})."
                )
            








def validate_total_selected_qty(doc, method):
    total_qty = sum(row.qty for row in doc.custom_item_locations)
    doc.custom_total_qty_selected = total_qty

# def on_submit_picklist(doc, method):
#     for item in doc.locations:  
#         if item.serial_no:
#             serial_numbers = item.serial_no.split("\n") 
#             for serial_no in serial_numbers:
#                 if serial_no:
#                     location = frappe.db.get_value("Serial No", serial_no, "warehouse")

#                     doc.append("custom_item_locations", {
#                         "item_code": item.item_code,
#                         "item_name": item.item_name,
#                         "qty": 1,  
#                         "serial_no": serial_no,
#                         "batch_no": item.batch_no,
#                         "location": location
#                     })

#     all_serial_no = []
#     for item in doc.locations:
#         if item.serial_no:
#             all_serial_no.extend(item.serial_no.split('\n'))

#     sorted_serial_no = sorted(all_serial_no, key=lambda x: int(x.replace('SN', '')))
#     doc.custom_all_item_serial_no_out = '\n'.join(sorted_serial_no)



@frappe.whitelist()
def populate_item_locations(doc, method):
    # """
    # Populate the custom_item_locations child table on submit with serial numbers
    # from the Serial No doctype, filtered by Custom_pl_customer, Custom_item_code,
    # and Warehouse != Default_loading_warehouse.
    # Follows FIFO logic based on serial number name (e.g., SN########) for the given quantity.
    # """

    # if not doc.custom_pl_customer or not doc.custom_item_code or not doc.custom_item_qty:
    #     return

    # # Get default loading warehouse from Warehouse Settings
    # # default_warehouse_doc = frappe.get_doc("Warehouse Settings", "name")
    # default_warehouse = doc.custom_loading_zone,
    # if not default_warehouse:
    #     frappe.throw(_("Please set Default Loading Warehouse in Warehouse Settings"))

    # qty_limit = int(doc.custom_item_qty)
    # tyre_type = doc.custom_item_type

    # # Get serial numbers using FIFO logic
    # serial_numbers = frappe.db.sql("""
    #     SELECT name, warehouse
    #     FROM `tabSerial No`
    #     WHERE
    #         custom_customer = %s
    #         AND item_code = %s
    #         AND warehouse != %s
    #         AND status = 'Active'
    #         AND (
    #             (custom_tyre_type = %s) 
    #             OR 
    #             (custom_tyre_type IS NULL AND %s IS NULL)
    #         )
    #     ORDER BY CAST(REPLACE(name, 'SN', '') AS UNSIGNED) ASC
    #     LIMIT %s
    # """, (doc.custom_pl_customer, doc.custom_item_code, default_warehouse, tyre_type, tyre_type, qty_limit), as_dict=1)

    # if len(serial_numbers) < doc.custom_item_qty:
    #     frappe.throw(
    #         _("Not enough serial numbers available for Item Code: {0}. Required: {1}, Available: {2}")
    #         .format(doc.custom_item_code, qty_limit, len(serial_numbers))
    #     )

    # # Clear existing entries in custom_item_locations
    # doc.custom_item_locations = []

    # # Get item name
    # item_name = frappe.db.get_value("Item", doc.custom_item_code, "item_name")

    # # Append serial numbers to custom_item_locations
    # for sr in serial_numbers:
    #     sr_doc = frappe.get_doc("Serial No", sr.name)
    #     doc.append("custom_item_locations", {
    #         "item_code": doc.custom_item_code,
    #         "item_name": item_name,
    #         "qty": 1,
    #         "serial_no": sr.name,          
    #         "batch_no": sr_doc.batch_no,
    #         "location": sr.warehouse,
    #         "target_warehouse": default_warehouse
    #     })

    # Sort and store all serial numbers
    all_serial_no = []
    for item in doc.custom_item_locations:
        if item.serial_no:
            all_serial_no.extend(item.serial_no.split('\n'))

    # Sort serial numbers numerically (assuming format 'SNxxxx')
    sorted_serial_no = sorted(all_serial_no, key=lambda x: int(x.replace('SN', '')))
    
    # Join sorted serial numbers and store in custom field
    doc.custom_all_item_serial_no_out = '\n'.join(sorted_serial_no)






@frappe.whitelist()
def populate_item_locations_json(doc, method):
    """
    Populate the custom_whole_items_details field with serial numbers
    from the Serial No doctype, filtered by Custom_pl_customer, Custom_item_code,
    and Warehouse != Default_loading_warehouse.
    Follows FIFO logic based on serial number name (e.g., SN########) for all available serials.
    """

    if not doc.custom_pl_customer or not doc.custom_item_code:
        return
    


    default_warehouse = doc.custom_loading_zone
    if not default_warehouse:
        frappe.throw(_("Please set Default Loading Warehouse in Warehouse Settings"))

    tyre_type = doc.custom_item_type
    

    # Fetch all matching serial numbers without qty limit
    serial_numbers = frappe.db.sql("""
        SELECT name, warehouse, batch_no
        FROM `tabSerial No`
        WHERE
            custom_customer = %s
            AND item_code = %s
            AND warehouse != %s
            AND status = 'Active'
            AND custom_type_of_warehouse = 'Location'
            AND (
                (custom_tyre_type = %s)
                OR
                (custom_tyre_type IS NULL AND %s IS NULL)
            )
        ORDER BY CAST(REPLACE(name, 'SN', '') AS UNSIGNED) ASC
    """, (doc.custom_pl_customer, doc.custom_item_code, default_warehouse, tyre_type, tyre_type), as_dict=1) or []

    # if not serial_numbers:
    #     frappe.throw(_("No serial numbers available for Item Code: {0}").format(doc.custom_item_code))

    # Get item name
    item_name = frappe.db.get_value("Item", doc.custom_item_code, "item_name")

    # Prepare data for custom_whole_items_details field
    whole_items_details = []
    for sr in serial_numbers:
        whole_items_details.append(
            f"Item Code: {doc.custom_item_code}, Item Name: {item_name}, Serial No: {sr.name}, Batch No: {sr.batch_no}, "
            f"Location: {sr.warehouse}, Target Warehouse: {default_warehouse}"
        )
    
    # Store data in custom_whole_items_details field
    doc.custom_whole_items_details = "\n".join(whole_items_details)

   

    doc.flags.ignore_permissions = True
    doc.db_update()
    frappe.db.commit()




































import frappe
from frappe.model.document import Document
from typing import Optional


class CustomDocument(Document):
    def update_child_table(self, fieldname: str, df: Optional["DocField"] = None):
        """Override to update only 'locations' field in Pick List and skip validation errors."""

        # if self.doctype != "Pick List" or fieldname != "locations":
        #     return  # Only execute if the doctype is 'Pick List' and field is 'locations'

        df: "DocField" = df or self.meta.get_field(fieldname)
        all_rows = self.get(df.fieldname) or []  # Ensure it's always a list

        # Skip validation and update only the 'locations' field
        for d in all_rows:
            if d:
                try:
                    d.db_update()
                except Exception:
                    pass  # Ignore any errors








def before_save_loc_val(self, method):
        """Ensure custom_item_locations is saved correctly and removed rows are deleted."""
        
        # Ensure all child table rows are properly linked to the parent
        for item in self.custom_item_locations:
            item.parent = self.name
            item.parentfield = "custom_item_locations"
            item.parenttype = "Pick List"

        # Fetch existing child table records from the DB
        existing_items = {d.name for d in frappe.get_all("Item Locations", filters={"parent": self.name}, fields=["name"])}
        current_items = {d.name for d in self.custom_item_locations if d.name}

        # Find deleted rows
        rows_to_delete = existing_items - current_items

        # Delete removed rows from the DB
        if rows_to_delete:
            for row in rows_to_delete:
                frappe.db.delete("Item Locations", {"name": row})

        # Explicitly save the child table
        self.set("custom_item_locations", self.custom_item_locations)







import frappe
from erpnext.stock.doctype.pick_list.pick_list import PickList

class CustomPickList(PickList):
    def validate_for_qty(self):
        """
        Completely skip the 'validate_for_qty' validation.
        """
        # Do nothing here to completely skip the original validation
        pass
