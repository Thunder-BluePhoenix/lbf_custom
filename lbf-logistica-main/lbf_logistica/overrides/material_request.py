import frappe
from frappe.model.document import Document
from frappe.utils import nowtime
import json
from erpnext.stock.doctype.shipment.shipment import Shipment
from frappe.contacts.doctype.address.address import get_address_display
from frappe.utils import flt
from lbf_logistica.overrides.serialno_barcode import before_save_serial, generate_document_barcode

# @frappe.whitelist()
# def create_pick_list(doc_name, method=None):
#     try:
#         # Fetch the Material Request document
#         material_request = frappe.get_doc("Material Request", doc_name)

#         # Ensure the custom_p_purpose is "Redelivery"
#         if material_request.custom_p_purpose != "Redelivery":
#             return []

#         pick_list_names = []
#         companies = frappe.get_all("Company", fields=["name"])

#         # Iterate through items in the material request
#         for item in material_request.items:
#             # Create a new Pick List document
#             pick_list = frappe.get_doc({
#                 "doctype": "Pick List",
#                 "custom_service": material_request.custom_service,
#                 "custom_p_purpose": material_request.custom_p_purpose,
#                 "custom_pl_customer": material_request.custom_customer_,
#                 "purpose": "Material Transfer",
#                 "material_request": material_request.name,
#                 "custom_item_code": item.item_code,
#                 "custom_item_name": item.item_name,
#                 "custom_item_qty": item.qty,
#                 "company": companies[0].get("name"),
#                 "custom_pl_status": "Open"
#             })

#             # Save the Pick List
#             pick_list.flags.ignore_permissions = True
#             pick_list.flags.ignore_mandatory = True
#             pick_list.db_update()

#             # Append the name of the created Pick List
#             pick_list_names.append(pick_list.name)

#         return pick_list_names

#     except Exception as e:
#         frappe.log_error(f"Error in create_pick_list: {str(e)}")
#         return []



# @frappe.whitelist() 
# def create_pick_list(doc_name, method=None): 
#     try: 
#         # Fetch the Material Request document 
#         material_request = frappe.get_doc("Material Request", doc_name) 

#         # Ensure the custom_p_purpose is "Redelivery" 
#         if material_request.custom_p_purpose != "Redelivery": 
#             return [] 

#         pick_list_names = [] 
#         companies = frappe.get_all("Company", fields=["name"]) 

#         # Check if Material Request has items
#         if not material_request.items:
#             frappe.throw("No items found in the Material Request.")

#         # Iterate through items in the material request 

#         # Iterate over each item in the Material Request's items child table
#         for item in material_request.items:
#             # Create a new Pick List document using new_doc
#             pick_list = frappe.new_doc("Pick List")
#             print(material_request.items,"11111111111111111111111")

#             # Set main Pick List fields
#             pick_list.custom_service = material_request.custom_service
#             pick_list.custom_p_purpose = material_request.custom_p_purpose
#             pick_list.custom_pl_customer = material_request.custom_customer_
#             pick_list.purpose = "Material Transfer"
#             pick_list.material_request = material_request.name
#             pick_list.company = material_request.company  # Assuming `company` is a field in the Material Request
#             pick_list.custom_pl_status = "Open"
#             pick_list.custom_item_code = item.item_code
#             pick_list.custom_item_name = item.item_name
#             pick_list.custom_item_qty =  item.qty

#             # Append locations data from the current item
#             pick_list.append("locations", {
#                 "item_code": item.item_code,
#                 "item_name": item.item_name,
#                 "qty": item.qty,
#                 "custom_target_warehouse": item.warehouse,
#                 "description": item.description,
#                 "item_group": item.item_group,
#                 "uom": item.uom,
#                 "conversion_factor": item.conversion_factor,
#                 "stock_uom": item.stock_uom,
#             })
#             print(pick_list.locations,"location")

            
#             pick_list.flags.ignore_permissions = True
#             # pick_list.insert()
#             # pick_list.submit()  # Submit the document if required
#             pick_list.db_update()

#             # Append the Pick List name to the list
#             pick_list_names.append(pick_list.name)

#             print(f"Created Pick List: {pick_list.name}")

#         return pick_list_names

#     except Exception as e: 
#         frappe.log_error(f"Error in create_pick_list: {str(e)}") 
#         return []


@frappe.whitelist()
def create_pick_list(doc_name):
    try:
        # Fetch the Material Request document
        material_request = frappe.get_doc("Material Request", doc_name)

        # Ensure the custom_p_purpose is "Redelivery"
        if material_request.custom_p_purpose != "Redelivery":
            return []

        pick_list_data = []
        companies = frappe.get_all("Company", fields=["name"])

        # Iterate through items in the material request
        if material_request.custom_service == "Peneus Hub":
            for item in material_request.items:
                # Create the data dictionary for Pick List
                pick_list_dict = {
                    "doctype": "Pick List",
                    "custom_service": material_request.custom_service,
                    "custom_p_purpose": material_request.custom_p_purpose,
                    "custom_pl_customer": material_request.custom_customer_,
                    "purpose": "Material Transfer",
                    "material_request": material_request.name,
                    "custom_loading_zone": material_request.custom_loading_zone,
                    "custom_item_code": item.item_code,
                    "custom_item_name": item.item_name,
                    "custom_item_qty": item.qty,
                    "company": companies[0].get("name"),
                    "custom_pl_status": "Open",
                    # "locations": [  
                    #     {
                    #         "item_code": item.item_code,
                    #         "qty": item.qty,
                    #         "stock_qty": item.qty,
                    #         # "custom_target_warehouse": item.warehouse,
                    #         # "description": item.description,
                    #         # "item_group": item.item_group,
                    #         # "uom": item.uom,
                    #         "conversion_factor": 1,
                    #         'use_serial_batch_fields': 1,
                    #         # "stock_uom": item.stock_uom
                    #     }
                    # ]
                }
                pick_list_data.append(pick_list_dict)
        

        if material_request.custom_service == "Tyre Hotel":
            for item in material_request.custom_th_items:
                # Create the data dictionary for Pick List
                pick_list_dict = {
                    "doctype": "Pick List",
                    "custom_service": material_request.custom_service,
                    "custom_p_purpose": material_request.custom_p_purpose,
                    "custom_pl_customer": material_request.custom_customer_,
                    "purpose": "Material Transfer",
                    "material_request": material_request.name,
                    "custom_loading_zone": material_request.custom_loading_zone,
                    "custom_item_code": item.item_code,
                    "custom_item_name": item.item_name,
                    "custom_item_qty": item.qty,
                    "custom_item_type": item.type,
                    "company": companies[0].get("name"),
                    "custom_pl_status": "Open",
                    # "locations": [  
                    #     {
                    #         "item_code": item.item_code,
                    #         "qty": item.qty,
                    #         "stock_qty": item.qty,
                    #         # "custom_target_warehouse": item.warehouse,
                    #         # "description": item.description,
                    #         # "item_group": item.item_group,
                    #         # "uom": item.uom,
                    #         "conversion_factor": 1,
                    #         'use_serial_batch_fields': 1,
                    #         # "stock_uom": item.stock_uom
                    #     }
                    # ]
                }
                pick_list_data.append(pick_list_dict)

        return pick_list_data

    except Exception as e:
        frappe.log_error(f"Error in create_pick_list: {str(e)}")
        return []


def create_pick_listfrom_hooks(doc,methode=None):
    try:
        # Ensure the custom_p_purpose is "Redelivery"
        if doc.custom_p_purpose != "Redelivery":
            return []

        pick_list_data = []
        created_picklists = []
        companies = frappe.get_all("Company", fields=["name"])

        # Iterate through items in the material request
        if doc.custom_service == "Peneus Hub":
            for item in doc.items:
                # Create the data dictionary for Pick List
                pick_list_dict = {
                    "doctype": "Pick List",
                    "custom_service": doc.custom_service,
                    "custom_p_purpose": doc.custom_p_purpose,
                    "custom_pl_customer": doc.custom_customer_,
                    "purpose": "Material Transfer",
                    "material_request": doc.name,
                    "custom_loading_zone": doc.custom_loading_zone,
                    "custom_shipping_to": doc.custom_shipping_to,
                    "custom_shipping_address_name": doc.custom_shipping_address_name,
                    "custom_shipping_address": doc.custom_address,
                    "custom_item_code": item.item_code,
                    "custom_item_name": item.item_name,
                    "custom_item_qty": item.qty,
                    "company": companies[0].get("name"),
                    "custom_pl_status": "Open",
                    # "locations": [  
                    #     {
                    #         "item_code": item.item_code,
                    #         "qty": item.qty,
                    #         "stock_qty": item.qty,
                    #         "conversion_factor": 1,
                    #         "use_serial_batch_fields": 1,
                    #     }
                    # ]
                }
                pick_list_data.append(pick_list_dict)

        if doc.custom_service == "Tyre Hotel":
            for item in doc.custom_th_items:
                # Create the data dictionary for Pick List
                pick_list_dict = {
                    "doctype": "Pick List",
                    "custom_service": doc.custom_service,
                    "custom_p_purpose": doc.custom_p_purpose,
                    "custom_pl_customer": doc.custom_customer_,
                    "purpose": "Material Transfer",
                    "material_request": doc.name,
                    "custom_loading_zone": doc.custom_loading_zone,
                    "custom_item_code": item.item_code,
                    "custom_item_name": item.item_name,
                    "custom_shipping_to": doc.custom_shipping_to,
                    "custom_shipping_address_name": doc.custom_shipping_address_name,
                    "custom_shipping_address": doc.custom_address,
                    "custom_item_qty": item.qty,
                    "custom_item_type": item.type,
                    "company": companies[0].get("name"),
                    "custom_pl_status": "Open",
                    # "locations": [  
                    #     {
                    #         "item_code": item.item_code,
                    #         "qty": item.qty,
                    #         "stock_qty": item.qty,
                    #         "conversion_factor": 1,
                    #         "use_serial_batch_fields": 1,
                    #     }
                    # ]
                }
                pick_list_data.append(pick_list_dict)

        # Insert Pick List documents
        for pick_list in pick_list_data:
            pick_list_doc = frappe.get_doc(pick_list)
            pick_list_doc.flags.ignore_permissions = True
            pick_list_doc.flags.ignore_links = True
            pick_list_doc.flags.ignore_mandatory = True
            pick_list_doc.flags.ignore_validate = True
            pick_list_doc.flags.ignore_global_search = True
            pick_list_doc.insert(ignore_permissions=True)
            created_picklists.append(pick_list_doc.name)  # Save the name of the Pick List

        # Submit the created Pick List documents
        for pick_list_name in created_picklists:
            pick_list_doc = frappe.get_doc("Pick List", pick_list_name)
            pick_list_doc.flags.ignore_permissions = True
            pick_list_doc.save()


    except Exception as e:
        frappe.log_error(f"Error in create_pick_list: {str(e)}")


    # for pick_list_name in created_picklists:
    #         pl_doc = frappe.get_doc("Pick List", pick_list_name)
    #         pl_doc.flags.ignore_permissions = True
    #         pl_doc.submit()

    # for pick_list in pick_list_data:
    #         pick_list_doc = frappe.get_doc(pick_list)
    #         pick_list_doc.flags.ignore_permissions = True
    #         # pick_list_doc.insert()
    #         pick_list_doc.submit()



@frappe.whitelist()
def add_locations_and_get_items(self, item_code, qty):
    # Add a new location to the Pick List
    self.append('locations', {
        'item_code': item_code,
        'qty': qty,
        'stock_qty': qty,
        'use_serial_batch_fields': 1
    })
    
    # Trigger get_item_locations method
    self.get_item_locations()
    
    # Save the document
    self.save()
    
    return True













def purpose_selection(doc, method=None):
    if doc.custom_p_purpose == "Redelivery":
        doc.material_request_type = "Material Transfer"




@frappe.whitelist()
def fetch_customer_address(customer):
    address = frappe.db.sql("""
        SELECT
            addr.address_title, addr.address_type, addr.address_line1, addr.city, addr.state, addr.pincode, addr.country
        FROM
            `tabAddress` addr
        JOIN
            `tabDynamic Link` links ON links.parent = addr.name
        WHERE
            links.link_name = %s AND links.link_doctype = 'Customer'
        LIMIT 1
    """, (customer,), as_dict=True)

    if address:
        addr = address[0]
        return f"""{addr.get('address_title', '')} · {addr.get('address_type', '')}
{addr.get('address_line1', '')}
{addr.get('city', '')}, {addr.get('state', '')}
PIN Code: {addr.get('pincode', '')}
{addr.get('country', '')}
        """
    return "No address found"


def update_req_qty(doc, method):
    total_qty = 0
    if doc.custom_service == "Peneus Hub":
        for item in doc.items:
            total_qty += item.qty or 0 
        doc.custom_required_qty = total_qty
    elif doc.custom_service == "Tyre Hotel":
        for item in doc.custom_th_items:
            total_qty += item.qty or 0 
        doc.custom_required_qty_th = total_qty




def create_bill_of_lading_and_shipment(doc, method):
    if doc.custom_service in ["Tyre Hotel", "Peneus Hub"]:
        original_on_submit = Shipment.on_submit

        def bypass_on_submit(self):
            self.db_set("status", "Submitted")

        Shipment.on_submit = bypass_on_submit

        try:
            # Fetch default company
            default_company = frappe.defaults.get_defaults().get("company")

            # Fetch address linked to the default company
            delivery_address_name = frappe.get_all(
                "Address",
                filters={"link_doctype": "Company", "link_name": default_company},
                fields=["name"],
                order_by="`tabAddress`.creation desc",
                limit=1
            )


            delivery_address = ""
            if delivery_address_name:
                delivery_address = get_address_display(delivery_address_name[0]["name"])

            # Fetch contact linked to the default company
            delivery_contact = frappe.get_all(
                "Contact",
                filters={"link_doctype": "Company", "link_name": default_company},
                fields=["name", "email_id", "phone"],
                order_by="`tabContact`.creation desc",
                limit=1
            )

            contact_name = delivery_contact[0]["name"] if delivery_contact else ""
            contact_details = delivery_contact[0]["phone"] if delivery_contact else ""

            # Create Shipment
            shipment = frappe.get_doc({
                "doctype": "Shipment",
                "material_request": doc.name,
                "transaction_date": doc.transaction_date,
                "custom_service_type": doc.custom_service,
                "custom_purpose": doc.custom_p_purpose,
                "custom_posting_date": doc.transaction_date,
                "custom_posting_time": doc.custom_posting_time,
                "custom_required_by": doc.schedule_date,
                "custom_season": doc.custom_season,
                "custom_license_plate": doc.custom_license_plate,
                "custom_mezzo": doc.custom_mezzo,
                "custom_condition": doc.custom_condition,
                "custom_reason": doc.custom_reason,
                "custom_pickup_from_th": doc.custom_party_type,
                "custom_tyre_dealer_name": doc.custom_customer_,
                "custom_tyre_dealer_address": doc.custom_address_of_customer,
                "delivery_to_type": "Company",
                "delivery_company": default_company,
                "delivery_address_name": delivery_address_name[0]["name"] if delivery_address_name else "",
                "delivery_address": delivery_address,
                "delivery_contact_name": contact_name,
                "delivery_contact": contact_details,
                "custom_shipment_parcel_th": [
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "schedule_date": item.schedule_date,
                        "qty": item.qty,
                        "warehouse": item.warehouse,
                        "uom": item.uom,
                        "type": item.type
                    }
                    for item in doc.custom_th_items
                ]
            })

            # Bypass validations and save Shipment
            shipment.flags.ignore_permissions = True
            shipment.flags.ignore_validate = True
            shipment.flags.ignore_mandatory = True
            shipment.insert(ignore_permissions=True)
            shipment.submit()

        finally:
            # Restore original on_submit
            Shipment.on_submit = original_on_submit

        legal_doc_for_redelivery = 1 if doc.custom_p_purpose == "Redelivery" else 0
        warehouse =frappe.get_doc("Warehouse Settings")
        source_warehouse = warehouse.default_source_warehouse
        target_warehouse = warehouse.default_target_warehouse
        default_loading_warehouse = doc.custom_loading_zone

        # Create Bill Of Lading
        if doc.custom_service == "Peneus Hub":
            bill_of_lading = frappe.get_doc({
                "doctype": "Bill Of Landing",
                "material_request": doc.name,
                "transaction_date": doc.transaction_date,
                "service": doc.custom_service,
                "reason": doc.custom_reason,
                "purpose": doc.custom_p_purpose,
                "posting_time": doc.custom_posting_time,
                "season": doc.custom_season,
                "condition": doc.custom_condition,
                "party_type": doc.custom_party_type,
                "total_qty":doc.custom_required_qty,
                "customer": doc.custom_customer_,
                "mezzo": doc.custom_mezzo,
                "season": doc.custom_season,
                "reason": doc.custom_reason,
                "condition": doc.custom_condition,
                "legal_doc_for_redelivery": legal_doc_for_redelivery,
                "reference_shipment_id": shipment.name,
                "reference_material_request": doc.name,
                "transporter_name":doc.custom_transporter_name,
                "accepted_warehouse": default_loading_warehouse or None,
                "shipping_to": doc.custom_shipping_to,
                "customer_shipping_address": doc.custom_shipping_address_name,
                "shipping_address": doc.custom_address,
                "customer_contact":doc.custom_customer_contact,
                "contact_person":doc.custom_contact_person,
                "contact":doc.custom_contact,
                "customer_address":doc.custom_shipping_address_name,
                "custom_transporter_name":doc.custom_transporter_address,
                "item_details_ph": [
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "schedule_date": item.schedule_date,
                        "total_qty": item.qty,
                        "warehouse": item.warehouse,
                        "uom": item.uom,
                    }
                    for item in doc.items
                ]
            })
        elif doc.custom_service == "Tyre Hotel":
            bill_of_lading = frappe.get_doc({
                "doctype": "Bill Of Landing",
                "naming_series":"MAT-PRE-TH-.YYYY.-.MM.-",
                "material_request": doc.name,
                "transaction_date": doc.transaction_date,
                "service": doc.custom_service,
                "reason": doc.custom_reason,
                "purpose": doc.custom_p_purpose,
                "posting_time": doc.custom_posting_time,
                "season": doc.custom_season,
                "condition": doc.custom_condition,
                "party_type": doc.custom_party_type,
                "customer": doc.custom_customer_,
                "total_qty":doc.custom_required_qty_th,
                "mezzo": doc.custom_mezzo,
                "season": doc.custom_season,
                "reason": doc.custom_reason,
                "condition": doc.custom_condition,
                "legal_doc_for_redelivery": legal_doc_for_redelivery,
                "reference_shipment_id": shipment.name,
                "reference_material_request": doc.name,
                "transporter_name":doc.custom_transporter_name,
                "accepted_warehouse": default_loading_warehouse or None,
                "shipping_to": doc.custom_shipping_to,
                "customer_shipping_address": doc.custom_shipping_address_name,
                "shipping_address": doc.custom_address,
                "customer_contact":doc.custom_customer_contact,
                "contact_person":doc.custom_contact_person,
                "contact":doc.custom_contact,
                "customer_address":doc.custom_shipping_address_name,
                "custom_transporter_name":doc.custom_transporter_address,
                "item_details_th": [
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "schedule_date": item.schedule_date,
                        "qty": item.qty,
                        "accepted_qty": 0,
                        "rejected_qty": 0,
                        "warehouse": item.warehouse,
                        "uom": item.uom,
                        "tyre_type": item.type,
                        "customer_batch_bundle": item.serial_and_batch_bundle
                    }
                    for item in doc.custom_th_items
                ]
            })
        bill_of_lading.save()

        if legal_doc_for_redelivery:
            bill_of_lading.submit()

    # # Pick List logic (unchanged)
    # if doc.custom_service == "PH" and doc.custom_p_purpose == "Redelivery":
    #     for item in doc.custom_th_items:
    #         pick_list = frappe.get_doc({
    #             "doctype": "Pick List",
    #             "custom_service": doc.custom_service,
    #             "custom_p_purpose": doc.custom_p_purpose,
    #             "custom_pl_customer": doc.custom_customer_,
    #             "purpose": "Material Transfer",
    #             "material_request": doc.name,
    #             "company": frappe.defaults.get_user_default("Company"),
    #             "custom_item_code": item.item_code,
    #             "custom_item_name": item.item_name,
    #             "custom_item_qty": item.qty,
    #             "custom_pl_status": "Open",
    #             "locations": [
    #                 {
    #                     "item_code": item.item_code,
    #                     "qty": item.qty,
    #                     "stock_qty": item.qty,
    #                     "conversion_factor": 1,
    #                     "use_serial_batch_fields": 1
    #                 }
    #             ]
    #         })
    #         pick_list.flags.ignore_permissions = True
    #         pick_list.insert()
    #         pick_list.submit()


@frappe.whitelist()
def create_item_from_material_request(row_data):
    if isinstance(row_data, str):
        row_data = json.loads(row_data)
    item_name = row_data.get('other_item_name')
    item_code = row_data.get('other_item_code')
    description = row_data.get('description')
    stock_uom = row_data.get('stock_uom')
    aspect_ratio = row_data.get('aspect_ratio_others')
    load_index = row_data.get('load_index_others')
    model = row_data.get('model_others')
    carcass = row_data.get('carcass_others')
    speed_rating = row_data.get('speed_rating_others')
    marks = row_data.get('marks_others')
    brand_name = row_data.get('brandothers')
    tire_widthmm = row_data.get('tire_widthmm_others')
    diameterinch = row_data.get('diameterinch_others')
    weight = row_data.get('weight_others')


    brand_doc = frappe.get_value("Brand", {"name": brand_name}, "name")
    
    if not brand_doc and brand_name:
        brand_doc = frappe.get_doc({
            "doctype": "Brand",
            "brand": brand_name
        })
        brand_doc.insert(ignore_permissions=True)
        frappe.db.commit()


    

    if not item_name or not stock_uom:
        frappe.throw("Item Name and Stock UOM are required to create an item.")

    item = frappe.get_doc({
        'doctype': 'Item',
        'item_name': item_name,
        'item_code': item_code,
        'item_group': 'All Item Groups',
        'description': description,
        'stock_uom': stock_uom,
        'is_stock_item': 1  ,
        'custom_tire_widthmm': tire_widthmm,
        'custom_aspect_ratio': aspect_ratio,
        'custom_carcass': carcass,
        'custom_diameterinch': diameterinch,
        'custom_load_index': load_index,
        'custom_speed_rating': speed_rating,
        'custom_weight': weight,
        'custom_model': model,
        'custom_marks': marks,
        'brand': brand_name
    })
    item.insert(ignore_permissions=True)
    frappe.db.commit()

    return item.item_code




def validate_submit(self, method = None):
    if self.custom_service == "Tyre Hotel" and self.custom_p_purpose == "Pick Up":
        for item in self.custom_th_items:
            if item.item_code == "Other":
                frappe.throw("Item with code 'Other' is not allowed to Submit the doc")










def create_serial_and_batch(self, method=None):
    if self.custom_service == "Tyre Hotel" and self.custom_p_purpose == "Pick Up":
           
            for item in self.custom_th_items:
                item_doc = frappe.get_doc("Item", item.item_code)
                accepted_qty = item.qty

                # Process Accepted Quantity
                if int(accepted_qty or 0) > 0:
                    if item_doc.has_batch_no:
                        batch_no = frappe.model.naming.make_autoname(item_doc.batch_number_series or "BATCH-.#####")
                        batch = frappe.get_doc({
                            "doctype": "Batch",
                            "batch_id": batch_no,
                            "item": item.item_code,
                            "batch_qty": accepted_qty,
                            "warehouse": "Special Customer Warehouse - LL",
                            "reference_doctype": "Material Request",
                            "reference_name": self.name,
                            "use_batchwise_valuation": 1
                        })
                        batch.flags.ignore_validate = True
                        batch.flags.ignore_permissions = True
                        batch.insert()
                        item.batch_no = batch_no

                    if item_doc.has_serial_no:
                        serial_nos = []
                        for i in range(int(accepted_qty or 0)):
                            serial_no = frappe.model.naming.make_autoname(item_doc.serial_no_series or "SERIAL-.#####")
                            serial_nos.append(serial_no)

                            custom_fields = {
                                "custom_tire_widthmm": item_doc.custom_tire_widthmm,
                                "custom_aspect_ratio": item_doc.custom_aspect_ratio,
                                "custom_carcass": item_doc.custom_carcass,
                                "custom_diameterinch": item_doc.custom_diameterinch,
                                "custom_load_index": item_doc.custom_load_index,
                                "custom_speed_rating": item_doc.custom_speed_rating,
                                "custom_weight": item_doc.custom_weight,
                                "custom_model": item_doc.custom_model,
                                "custom_marks": item_doc.custom_marks,
                                "brand": item_doc.brand
                            }

                            serial = frappe.get_doc({
                                "doctype": "Serial No",
                                "serial_no": serial_no,
                                "item_code": item.item_code,
                                "batch_no": item.batch_no or "",
                                "warehouse": "Special Customer Warehouse - LL",
                                "custom_creation_reference_doctype": "Material Request",
                                "custom_creation_document_name": self.name,
                                "status": "Active",
                                "custom_service": self.custom_service,
                                "custom_license_plate": self.custom_license_plate,
                                "custom_customer": self.custom_customer_,
                                "custom_tyre_type": item.type,
                                **custom_fields
                            })
                            serial.flags.ignore_validate = True
                            serial.flags.ignore_permissions = True
                            before_save_serial(serial, method=None)
                            serial.save()
                        item.serial_nos = "\n".join(serial_nos)
                        

                

                
                create_serial_and_batch_bundle(self, item)
                self.save()
                # update_mr_ins_log(self, method = None)

            # all_serial_no = []
            # for item in self.item_details_th:
            #     if item.serial_no:
            #         all_serial_no.extend(item.serial_no.split('\n'))

            # sorted_serial_no = sorted(all_serial_no, key=lambda x: int(x.replace('SN', '')))
            # self.all_item_serial_no = '\n'.join(sorted_serial_no)
            # self.status = "Closed"



def create_serial_and_batch_bundle(self, item):
        """
        Create separate Serial and Batch Bundles for accepted and rejected quantities of an item.
        """

        default_company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

        # Create Serial and Batch Bundle for Accepted Quantity
        if int(item.qty or 0) > 0:
            bundle_doc_accepted = frappe.new_doc("Serial and Batch Bundle")
            bundle_doc_accepted.item_code = item.item_code
            bundle_doc_accepted.item_name = item.item_name
            bundle_doc_accepted.company = default_company
            bundle_doc_accepted.warehouse = "Special Customer Warehouse - LL"
            bundle_doc_accepted.type_of_transaction = "Inward"
            bundle_doc_accepted.voucher_type = "Material Request"
            bundle_doc_accepted.voucher_no = self.name
            bundle_doc_accepted.total_qty = flt(item.qty)
            bundle_doc_accepted.custom_is_active =1
            bundle_doc_accepted.custom_customer = self.custom_customer_

            valuation_rate = frappe.db.get_value("Item", item.item_code, "valuation_rate") or 0

            # Populate Serial and Batch Table for Accepted Quantity
            serial_nos_accepted = item.serial_nos.split("\n") if item.serial_nos else []
            for serial_no in serial_nos_accepted:
                bundle_doc_accepted.append("entries", {
                    "serial_no": serial_no,
                    "batch_no": item.batch_no or "",
                    "qty": 1,
                    "warehouse": "Special Customer Warehouse - LL",
                    "valuation_rate": valuation_rate
                })

            bundle_doc_accepted.flags.ignore_mandatory = True
            bundle_doc_accepted.flags.ignore_validate = True
            bundle_doc_accepted.flags.ignore_permissions = True
            bundle_doc_accepted.insert()
            bundle_doc_accepted.submit()

            item.serial_and_batch_bundle = bundle_doc_accepted.name
        

            # Create Ledger Entry for Accepted Quantity
            # self.create_ledger_entry(bundle_doc_accepted)



def create_ledger_entry(doc, bundle_doc):
    """
    Create ledger entry for the submitted Serial and Batch Bundle
    """
    ledger_entry = frappe.new_doc("Stock Ledger Entry")
    ledger_entry.item_code = bundle_doc.item_code
    ledger_entry.warehouse = bundle_doc.warehouse
    ledger_entry.company = bundle_doc.company
    ledger_entry.voucher_type = bundle_doc.voucher_type
    ledger_entry.voucher_no = bundle_doc.voucher_no
    ledger_entry.serial_and_batch_bundle = bundle_doc.name  # Link the bundle
    ledger_entry.actual_qty = bundle_doc.total_qty
    ledger_entry.qty_change = bundle_doc.total_qty  # Matches total_qty
    ledger_entry.qty_after_transaction = bundle_doc.total_qty  # Assuming stock was zero before
    ledger_entry.incoming_rate = 0  # Adjust as necessary
    ledger_entry.valuation_rate = 0  # Adjust as necessary
    ledger_entry.balance_stock_value = 0  # Adjust as necessary
    ledger_entry.change_in_stock_value = 0  # Adjust as necessary
    ledger_entry.posting_date = frappe.utils.nowdate()
    ledger_entry.posting_time = frappe.utils.nowtime()
    ledger_entry.fiscal_year = frappe.defaults.get_user_default("fiscal_year")
    ledger_entry.auto_created_serial_and_batch_bundle = 1
    ledger_entry.flags.ignore_mandatory = True
    ledger_entry.flags.ignore_validate = True
    ledger_entry.flags.ignore_permissions = True
    ledger_entry.insert()
    ledger_entry.submit()




def update_mr_ins_log(self, method=None):
    if not self.custom_material_request_instruction_log:
        return  


    mr_log = frappe.get_doc("Material Request Instruction Log", self.custom_material_request_instruction_log)
    mr_log.material_request_doc = self.name
    mr_log.material_request_submitted = 1


    if mr_log.material_request_type == "Pick Up":
        mr_log.labels_ready_for_print = 1
        mr_items_map = {mr_item.id: mr_item for mr_item in mr_log.th_items}


        for item in self.custom_th_items:
            if item.id in mr_items_map:
                mr_items_map[item.id].serial_and_batch_bundle = item.serial_and_batch_bundle
                mr_items_map[item.id].serial_nos = item.serial_nos


    mr_log.save()





