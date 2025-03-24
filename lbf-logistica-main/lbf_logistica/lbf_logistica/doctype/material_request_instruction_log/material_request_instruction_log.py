# Copyright (c) 2024, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowtime, flt
from frappe import _
from datetime import datetime
from frappe.utils import nowtime, nowdate
from lbf_logistica.overrides.serialno_barcode import before_save_serial, generate_document_barcode
from datetime import datetime, timedelta
import calendar



class MaterialRequestInstructionLog(Document):
        def validate(self):
            if self.service == "Peneus Hub":
                item_qty_map = {}

                for item in self.items:
                    if not item.item_code:
                        frappe.throw(_("Item Code is required for row {0}.").format(item.idx))

                    if item.item_code in item_qty_map:
                        item_qty_map[item.item_code] += item.qty
                    else:
                        item_qty_map[item.item_code] = item.qty

                # Validate against available stock
                customer = self.customer
                for item_code, total_qty in item_qty_map.items():
                    total_actual_qty = get_total_actual_qty(item_code, customer)

                    if total_actual_qty < total_qty:
                        frappe.throw(_("The total quantity ({0}) entered for item {1} exceeds available stock ({2}) for customer {3}.").format(
                            total_qty, item_code, total_actual_qty, customer))
                        
        def before_save(self):
            current_weekday = datetime.strptime(nowdate(), "%Y-%m-%d").strftime("%A")
            self.posting_day = current_weekday
            total_qty = 0
            if self.service == "Peneus Hub":
                for item in self.items:
                    total_qty += item.qty or 0 
                self.total_qty = total_qty
            elif self.service == "Tyre Hotel":
                for item in self.th_items:
                    total_qty += item.qty or 0 
                self.required_qty_th = total_qty
                for index, item in enumerate(self.th_items, start=1):
                    item.id = f"Index_{index}"



            validate_item_qty(self, method = None)
            


        def before_submit(self):
            time_threshold(self)


            




def check_time_before_submit(doc, method):
    timeline_settings = frappe.get_doc("Notification and Timeline Settings")
    if timeline_settings.start_time is None or timeline_settings.ending_time is None:
         return
    start_time = timeline_settings.start_time
    end_time = timeline_settings.ending_time
    
    current_time = nowtime()
	
    
    if not (start_time <= current_time <= end_time):
        frappe.throw(
            f"Submission not allowed at this time. Allowed timing is between {start_time} and {end_time}."
        )


def create_material_request(doc, method):
    # Create a new Material Request
    if doc.service == "Peneus Hub":
        material_request = frappe.new_doc("Material Request")
        material_request.custom_service = doc.service
        material_request.transaction_date = doc.transaction_date
        material_request.schedule_date = doc.schedule_date
        material_request.custom_posting_time = doc.posting_time
        material_request.custom_p_purpose = doc.material_request_type
        material_request.custom_customer_ = doc.customer
        material_request.custom_address_of_customer = doc.address_of_customer
        material_request.custom_shipping_address_name = doc.shipping_address_name
        material_request.custom_contact_person = doc.contact_person
        material_request.custom_contact = doc.contact
        material_request.custom_transporter_preference = doc.transporter_preference
        material_request.custom_transporter_name = doc.transporter_name
        material_request.custom_party_type = doc.party_type
        material_request.custom_transporter_name = doc.transporter_name
        material_request.custom_transporter_address = doc.transporter_address
        material_request.custom_shipping_to = doc.shipping_to
        material_request.custom_customer_contact= doc.customer_contact
        material_request.custom_address = doc.address
        material_request.custom_posting_day = doc.posting_day
        material_request.custom_material_request_instruction_log = doc.name
        material_request.custom_availability_threshold_minutes = doc.availability_threshold
        material_request.custom_mrl_submitted_between_available_threshold = doc.submitted_between_available_threshold
        if doc.weekdays_off:
            material_request.custom_weekdays_off = []
            for weekday in doc.weekdays_off:
                row = material_request.append('custom_weekdays_off', {})
                
                for field in weekday.as_dict():
                    if field not in ['name', 'owner', 'creation', 'modified', 'modified_by', 'parent', 'parentfield', 'parenttype', 'idx']:
                        row.set(field, weekday.get(field))


        for item in doc.items:
            material_request.append("items", {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "schedule_date": item.schedule_date,
                "qty": item.qty,
                "warehouse": item.warehouse,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": item.conversion_factor,
                "description": item.description,
                "project": item.project,
                "cost_center": item.cost_center,
                "custom_max_order_qty": item.custom_max_order_qty
            })

        # Save and submit the Material Request
        material_request.save(ignore_permissions=True)
        # timeline_settings = frappe.get_doc("Notification and Timeline Settings")
        # if timeline_settings.start_time is None or timeline_settings.ending_time is None:
        #     return
        # start_time = timeline_settings.start_time
        # end_time = timeline_settings.ending_time

        # weekly_off_days = []
        if doc.transporter_name:
            weekly_off_days = frappe.get_all(
            "Weekdays Table", 
            filters={"parent": doc.transporter_name},
            pluck="weekday"  # Fetch the linked Weekday values
        )
        print(weekly_off_days, "weekly_off_days")

        # Get current weekday
        current_weekday = datetime.strptime(nowdate(), "%Y-%m-%d").strftime("%A")

        
        # Get current weekday
        current_weekday = datetime.strptime(nowdate(), "%Y-%m-%d").strftime("%A")
        print(current_weekday, "current_weekday")
        start_time = None
        end_time = None
        if doc.transporter_name:
            start_time, end_time = frappe.get_value(
                "Supplier", doc.transporter_name, ["custom_cutoff_start_time", "custom_cutoff_end_time"]
            )
        current_time = datetime.strptime(nowtime().split(".")[0], "%H:%M:%S").time()
        is_weekly_off = current_weekday in weekly_off_days
        print(is_weekly_off, "is_weekly_off")

        if is_weekly_off:
            frappe.msgprint(f"Material Request is saved as draft because today is a weekly off day for {doc.transporter_name}.")
            material_request.save(ignore_permissions=True)  # Keep in draft
        else:
            if start_time and end_time:
                start_time = datetime.strptime(str(start_time), "%H:%M:%S").time()
                end_time = datetime.strptime(str(end_time), "%H:%M:%S").time()
                print(type(start_time), type(current_time), type(end_time), "jjjjjjjjjjjjjjjjjj")
                
                if start_time <= current_time <= end_time:
                    material_request.submit()
                else:
                    frappe.msgprint(f"Material Request is saved as draft because the current time ({current_time}) is outside the allowed cutoff time ({start_time} - {end_time}).")
                    material_request.save(ignore_permissions=True)  # Keep in draft
            else:
                material_request.submit()  # If no cutoff time is defined, submit by default


        frappe.msgprint(
            f"Material Request {material_request.name} has been created and Submitted successfully for {doc.service}."
        )

    elif doc.service == "Tyre Hotel":
        material_request = frappe.new_doc("Material Request")
        material_request.custom_service = doc.service
        material_request.transaction_date = doc.transaction_date
        material_request.schedule_date = doc.schedule_date
        material_request.custom_posting_time = doc.posting_time
        material_request.custom_p_purpose = doc.material_request_type
        material_request.custom_customer_ = doc.customer
        material_request.custom_address_of_customer = doc.address_of_customer
        material_request.custom_shipping_address_name = doc.shipping_address_name
        material_request.custom_contact_person = doc.contact_person
        material_request.custom_contact = doc.contact
        material_request.custom_transporter_preference = doc.transporter_preference
        material_request.custom_transporter_name = doc.transporter_name
        material_request.custom_season = doc.season
        material_request.custom_license_plate = doc.license_plate
        material_request.custom_mezzo = doc.mezzo
        material_request.custom_condition = doc.condition
        material_request.custom_reason = doc.reason
        material_request.custom_contact_person_of_cp = doc.contact_person_of_cp
        material_request.custom_contact_of_cp = doc.contact_of_cp
        material_request.custom_party_type = doc.party_type
        material_request.custom_required_qty_th = doc.required_qty_th
        material_request.custom_transporter_name = doc.transporter_name
        material_request.custom_transporter_address = doc.transporter_address
        material_request.custom_shipping_to = doc.shipping_to
        material_request.custom_customer_contact= doc.customer_contact
        material_request.custom_address = doc.address
        material_request.custom_posting_day = doc.posting_day
        material_request.custom_email = doc.email
        material_request.custom_material_request_instruction_log = doc.name
        material_request.custom_availability_threshold_minutes = doc.availability_threshold
        material_request.custom_mrl_submitted_between_available_threshold = doc.submitted_between_available_threshold
        if doc.weekdays_off:
            material_request.custom_weekdays_off = []
            for weekday in doc.weekdays_off:
                row = material_request.append('custom_weekdays_off', {})
                
                for field in weekday.as_dict():
                    if field not in ['name', 'owner', 'creation', 'modified', 'modified_by', 'parent', 'parentfield', 'parenttype', 'idx']:
                        row.set(field, weekday.get(field))


        has_restricted_item = False

        for item in doc.th_items:

            if "other" in item.item_code.lower() or "other" in item.item_name.lower():
                has_restricted_item = True  
            material_request.append("custom_th_items", {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "other_item_code":item.other_item_code,
                "other_item_name":item.other_item_name,
                "schedule_date": item.schedule_date,
                "qty": item.qty,
                "warehouse": item.warehouse,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": item.conversion_factor,
                "description": item.description,
                "project": item.project,
                "cost_center": item.cost_center,
                "type":item.type,
                "max_order_qty": item.max_order_qty,
                "diameterinch_others":item.diameterinch_others,
                "tire_widthmm_others":item.tire_widthmm_others,
                "model_others":item.model_others,
                "weight_others":item.weight_others,
                "aspect_ratio_others":item.aspect_ratio_others,
                "load_index_others":item.load_index_others,
                "carcass_others":item.carcass_others,
                "speed_rating_others":item.speed_rating_others,
                "marks_others":item.marks_others,
                "brandothers":item.brandothers,
                "id": item.id
            })

        # Save and submit the Material Request.max_order_qty
        material_request.flags.ignore_validate = True
        material_request.save(ignore_permissions=True)
        
        # timeline_settings = frappe.get_doc("Notification and Timeline Settings")
        # if timeline_settings.start_time is None or timeline_settings.ending_time is None:
        #     return
        # start_time = timeline_settings.start_time
        # end_time = timeline_settings.ending_time

        if doc.transporter_name:
            weekly_off_days = frappe.get_all(
            "Weekdays Table", 
            filters={"parent": doc.transporter_name},
            pluck="weekday"  # Fetch the linked Weekday values
        )
        print(weekly_off_days, "weekly_off_days")

     

        # Get current weekday
        current_weekday = datetime.strptime(nowdate(), "%Y-%m-%d").strftime("%A")
        print(current_weekday, "current_weekday")
        start_time = None
        end_time = None

        if doc.transporter_name:
            start_time, end_time = frappe.get_value(
                "Supplier", doc.transporter_name,  ["custom_cutoff_start_time", "custom_cutoff_end_time"]
            )

        current_time = datetime.strptime(nowtime().split(".")[0], "%H:%M:%S").time()
        is_weekly_off = current_weekday in weekly_off_days
        print(is_weekly_off, "is_weekly_off")
        print(is_weekly_off, "is_weekly_off")


        if not has_restricted_item:
            doc.material_request_doc = material_request.name
            doc.save()
            if is_weekly_off:
                frappe.msgprint(f"Material Request is saved as draft because today is a weekly off day for {doc.transporter_name}.")
                material_request.save(ignore_permissions=True)  # Keep in draft
                doc.material_request_doc = material_request.name
                doc.save()
                
            else:
                if not has_restricted_item and start_time and end_time:
                    start_time = datetime.strptime(str(start_time), "%H:%M:%S").time()
                    end_time = datetime.strptime(str(end_time), "%H:%M:%S").time()
                    print(type(start_time), type(current_time), type(end_time), "jjjjjjjjjjjjjjjjjj")
                    
                    if start_time <= current_time <= end_time:
                        material_request.submit()
                    else:
                        frappe.msgprint(f"Material Request is saved as draft because the current time ({current_time}) is outside the allowed cutoff time ({start_time} - {end_time}).")
                        material_request.save(ignore_permissions=True)  # Keep in draft
                else:
                    material_request.submit()  # If no cutoff time is defined, submit by default

        else:
            frappe.msgprint(f"Material Request is saved as draft because The Item does not exist in current database")
            material_request.save(ignore_permissions=True) 
            doc.material_request_doc = material_request.name
            doc.save()



        


        frappe.msgprint(
            f"Material Request {material_request.name} has been created for {doc.service}."
        )


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


@frappe.whitelist()
def fetch_supplier_address(supplier):
    address = frappe.db.sql("""
        SELECT
            addr.address_title, addr.address_type, addr.address_line1, addr.city, addr.state, addr.pincode, addr.country
        FROM
            `tabAddress` addr
        JOIN
            `tabDynamic Link` links ON links.parent = addr.name
        WHERE
            links.link_name = %s AND links.link_doctype = 'Supplier'
        LIMIT 1
    """, (supplier,), as_dict=True)

    if address:
        addr = address[0]
 
       
        return f"""{addr.get('address_title', '')} · {addr.get('address_type', '')}
{addr.get('address_line1', '')} 
{addr.get('city', '')}, {addr.get('state', '')}  
PIN Code: {addr.get('pincode', '')} 
{addr.get('country', '')}
        """
   
    return "No address found"


import frappe

@frappe.whitelist()
def get_item_codes_for_customer(customer):
    if not customer:
        return []
    
    # Fetch distinct item codes linked to the customer via Serial No
    item_codes = frappe.db.get_list(
        'Serial No',
        filters={'custom_customer': customer, 'status': 'Active'},
        pluck='item_code'
    )

    # Remove duplicates by converting to a set, then back to a list
    unique_item_codes = list(set(item_codes))
    return unique_item_codes


# @frappe.whitelist()
# def get_th_item_codes_for_customer(customer, license_plate = None):
#     if not customer:
#         return []
    
#     # Fetch distinct item codes linked to the customer via Serial No
#     if license_plate:
#         item_codes = frappe.db.get_list(
#             'Serial No',
#             filters={'custom_customer': customer, 'status': 'Active', 'custom_license_plate':license_plate, 'custom_tyre_type': ['!=', ''], 'item_code': ['!=', 'Other'] },
#             pluck='item_code'
#         )
#     else:
#         item_codes = frappe.db.get_list(
#         'Serial No',
#         filters={'custom_customer': customer, 'status': 'Active', 'custom_tyre_type': ['!=', ''], 'item_code': ['!=', 'Other']},
#         pluck='item_code'
#     )
    
#     # Remove duplicates by converting to a set, then back to a list
#     unique_item_codes = list(set(item_codes))

#     print ("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", unique_item_codes)
#     return unique_item_codes









# @frappe.whitelist()
# def get_th_item_codes_for_customer(customer, license_plate=None):
#     if not customer:
#         return []
    
#     # Define fields to fetch
#     fields = ['item_code', 'custom_tyre_type']
    
#     # Fetch items linked to the customer via Serial No
#     if license_plate:
#         serial_data = frappe.db.get_all(
#             'Serial No',
#             filters={
#                 'custom_customer': customer, 
#                 'status': 'Active', 
#                 'custom_license_plate': license_plate,
#                 'custom_tyre_type': ['!=', ''],
#                 'item_code': ['!=', 'Other']
#             },
#             fields=fields
#         )
#     else:
#         serial_data = frappe.db.get_all(
#             'Serial No',
#             filters={
#                 'custom_customer': customer, 
#                 'status': 'Active',
#                 'custom_tyre_type': ['!=', ''],
#                 'item_code': ['!=', 'Other']
#             },
#             fields=fields
#         )
    
#     # Create a unique list based on item_code AND custom_tyre_type combination
#     unique_items = {}
#     for item in serial_data:
#         # Create a composite key using both item_code and custom_tyre_type
#         composite_key = f"{item.item_code}_{item.custom_tyre_type}"
        
#         if composite_key not in unique_items:
#             # Fetch the item_name for each unique combination
#             item_name = frappe.db.get_value('Item', item.item_code, 'item_name')
#             unique_items[composite_key] = {
#                 'item_code': item.item_code,
#                 'item_name': item_name,
#                 'custom_tyre_type': item.custom_tyre_type
#             }
#     print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", list(unique_items.values()))
#     return list(unique_items.values())

# @frappe.whitelist()
# def search_th_items_for_link_field(doctype, txt, searchfield, start, page_len, filters):
#     """
#     Standard search function for link fields that accepts the standard Frappe link search parameters
#     """
#     customer = filters.get('customer')
#     license_plate = filters.get('license_plate')
    
#     if not customer:
#         return []
    
#     items_data = get_th_item_codes_for_customer(customer, license_plate)
    
#     # Filter by the search text if provided
#     if txt:
#         txt = txt.lower()
#         filtered_items = [
#             item for item in items_data 
#             if txt in item['item_code'].lower() or 
#                txt in (item['item_name'] or '').lower() or 
#                txt in (item['custom_tyre_type'] or '').lower()
#         ]
#     else:
#         filtered_items = items_data
    
#     # Format for link field results: (value, description)
#     results = []
#     for item in filtered_items:
#         # Create a formatted description with item name and tyre type
#         description = f"{item['item_name']} | Type: {item['custom_tyre_type']}"
#         results.append((item['item_code'], description))
    
#     return results



 



# @frappe.whitelist()
# def get_th_item_codes_for_customer(customer, license_plate=None):
#     if not customer:
#         return []
    
#     filters = {
#         'custom_customer': customer,
#         'status': 'Active',
#         'custom_tyre_type': ['!=', '']
#     }
    
#     if license_plate:
#         filters['custom_license_plate'] = license_plate
    
#     items_data = frappe.db.get_list(
#         'Serial No',
#         filters=filters,
#         fields=['item_code', 'item_name', 'custom_tyre_type']
#     )
    
#     unique_items = []
#     seen_combinations = set()
    
#     for item in items_data:
#         key = f"{item.item_code}_{item.custom_tyre_type}"
        
#         if key not in seen_combinations:
#             seen_combinations.add(key)
#             unique_items.append(item)
    
#     return unique_items





@frappe.whitelist()
def search_th_items_for_link_field(doctype, txt, searchfield, start, page_len, filters):
    """
    Search function that returns distinct combinations of item_code and tyre_type
    """
    customer = filters.get('customer')
    license_plate = filters.get('license_plate')
    
    if not customer:
        return []
    
    # Define fields to fetch
    fields = ['item_code', 'custom_tyre_type']
    
    # Build filters
    search_filters = {
        'custom_customer': customer, 
        'status': 'Active',
        'custom_tyre_type': ['!=', ''],
        'custom_type_of_warehouse': 'Location',
        'item_code': ['!=', 'Other']
    }
    
    if license_plate:
        search_filters['custom_license_plate'] = license_plate
    
    # Add text search condition
    if txt:
        search_filters.update({
            'item_code': ['like', f'%{txt}%']
        })
    
    # Fetch items linked to the customer via Serial No
    serial_data = frappe.db.get_all(
        'Serial No',
        filters=search_filters,
        fields=fields,
        distinct=True
    )
    
    # Create a unique list based on item_code AND custom_tyre_type combination
    results = []
    seen_combinations = set()
    
    for item in serial_data:
        # Create a composite key using both item_code and custom_tyre_type
        composite_key = f"{item.item_code}_{item.custom_tyre_type}"
        
        if composite_key not in seen_combinations:
            seen_combinations.add(composite_key)
            
            # Fetch the item_name for each unique combination
            item_name = frappe.db.get_value('Item', item.item_code, 'item_name')
            
            # Format display: Item Code | Item Name | Type: Tyre Type
            display_value = f"{item.item_code} | {item_name} | Type: {item.custom_tyre_type}"
            
            # For Frappe link field format: (value, description)
            results.append((item.item_code, display_value))
    print("PL:", results)
    return results

@frappe.whitelist()
def get_item_tyre_type(customer, item_code, license_plate=None):
    """Get the tyre type for a specific item and customer"""
    filters = {
        'custom_customer': customer,
        'status': 'Active',
        'item_code': item_code,
        'custom_type_of_warehouse': 'Location',
        'custom_tyre_type': ['!=', '']
    }
    
    if license_plate:
        filters['custom_license_plate'] = license_plate
    
    # Get the most recent or most common tyre type for this item
    result = frappe.db.get_value('Serial No', filters, 'custom_tyre_type')
    return result




@frappe.whitelist()
def get_total_actual_qty(item_code, customer=None):
    if not item_code:
        return 0

    values = [item_code]
    conditions = ["sn.status = 'Active'", "sn.custom_type_of_warehouse = 'Location'", "sn.item_code = %s", "sn.custom_tyre_type = ''"]

    if customer:
        conditions.append("sn.custom_customer = %s")
        values.append(customer)


    total_actual_qty = frappe.db.sql(f"""
        SELECT COUNT(sn.name)
        FROM `tabSerial No` sn
        WHERE {" AND ".join(conditions)}
    """, tuple(values))

    # Return the total count or 0 if no entries exist
    return total_actual_qty[0][0] if total_actual_qty and total_actual_qty[0][0] else 0









@frappe.whitelist()
def get_total_actual_qty_for_th(item_code, customer=None, tyre_type=None, license_plate=None):
    if not item_code:
        return 0

    conditions = ["sn.status = 'Active'", "sn.item_code = %s", "sn.custom_type_of_warehouse = 'Location'"]
    values = [item_code]

    if customer:
        conditions.append("sn.custom_customer = %s")
        values.append(customer)

    if tyre_type:
        conditions.append("sn.custom_tyre_type = %s")
        values.append(tyre_type)

    if license_plate:
        conditions.append("sn.custom_license_plate = %s")
        values.append(license_plate)

    total_actual_qty = frappe.db.sql(f"""
        SELECT COUNT(sn.name)
        FROM `tabSerial No` sn
        WHERE {" AND ".join(conditions)}
    """, tuple(values))

    return total_actual_qty[0][0] if total_actual_qty and total_actual_qty[0][0] else 0








@frappe.whitelist()
def get_items_with_others(doctype, txt, searchfield, start, page_len, filters):
    customer = filters.get("customer", None)

    items = frappe.db.sql("""
        SELECT name 
        FROM `tabItem` 
        WHERE name LIKE %s 
        LIMIT %s, %s
    """, (f"%{txt}%", start, page_len))

    if not items and txt.lower() != "other":
        items = [("Other",)]

    return items



def validate_item_qty(doc, method = None):
    if doc.material_request_type == "Redelivery" and doc.service == "Peneus Hub":
        item_qty_map = {}
        
        # Group total quantities by item_code
        for item in doc.items:
            if item.item_code:
                avl_qty = get_total_actual_qty(item.item_code, doc.customer)
                item.custom_max_order_qty = avl_qty
                item_qty_map[item.item_code] = item_qty_map.get(item.item_code, 0) + (item.qty or 0)
        
        # Check stock for each item
        for item_code, total_qty in item_qty_map.items():
            actual_qty = get_total_actual_qty(item_code, doc.customer)
            
            if total_qty > actual_qty:
                frappe.throw(
                    _('The total quantity ({0}) entered for item {1} exceeds available stock ({2}) for customer {3}.')
                    .format(total_qty, item_code, actual_qty, doc.customer)
                )

    if doc.material_request_type == "Redelivery" and doc.service == "Tyre Hotel":
        item_qty_map = {}

        # Group total quantities by item_code and tyre_type
        for item in doc.th_items:
            if item.item_code and item.type:

                avl_qty = get_total_actual_qty_for_th(item.item_code, doc.customer, item.type)
                item.max_order_qty = avl_qty
                key = (item.item_code, item.type)
                item_qty_map[key] = item_qty_map.get(key, 0) + (item.qty or 0)

        # Check stock for each (item_code, tyre_type) combination
        for (item_code, tyre_type), total_qty in item_qty_map.items():
            actual_qty = get_total_actual_qty_for_th(item_code, doc.customer, tyre_type)  # Fixed function call

            if total_qty > actual_qty:
                frappe.throw(
                    _('The total quantity ({0}) entered for item {1} (Tyre Type: {2}) exceeds available stock ({3}) for customer {4}.')
                    .format(total_qty, item_code, tyre_type, actual_qty, doc.customer)
                )




@frappe.whitelist()
def get_child_customers(customer_name):
    if not customer_name:
        return []

    child_customers = frappe.get_all(
        "Child Customer",
        filters={"parent": customer_name},
        fields=["customer"]
    )

    customer_list = [d["customer"] for d in child_customers]
    customer_list.append(customer_name)  

    return customer_list























def create_serial_and_batch(self, method=None):
    if self.service == "Tyre Hotel" and self.material_request_type == "Pick Up":
           
            for item in self.th_items:
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
                            "reference_doctype": "Material Request Instruction Log",
                            "reference_name": self.name,
                            "use_batchwise_valuation": 1
                        })
                        batch.flags.ignore_validate = True
                        batch.flags.ignore_permissions = True
                        batch.insert()
                        item.batch_no = batch_no

                    if item_doc.has_serial_no:
                        serial_nos = []
                        for i in range(int(item.accepted_qty or 0)):
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
                                "custom_creation_reference_doctype": "Bill Of Landing",
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
                        item.serial_no = "\n".join(serial_nos)

                

                
                self.create_serial_and_batch_bundle(item)

            all_serial_no = []
            for item in self.item_details_th:
                if item.serial_no:
                    all_serial_no.extend(item.serial_no.split('\n'))

            sorted_serial_no = sorted(all_serial_no, key=lambda x: int(x.replace('SN', '')))
            self.all_item_serial_no = '\n'.join(sorted_serial_no)
            self.status = "Closed"



def create_serial_and_batch_bundle(self, item):
        """
        Create separate Serial and Batch Bundles for accepted and rejected quantities of an item.
        """

        default_company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

        # Create Serial and Batch Bundle for Accepted Quantity
        if int(item.accepted_qty or 0) > 0:
            bundle_doc_accepted = frappe.new_doc("Serial and Batch Bundle")
            bundle_doc_accepted.item_code = item.item_code
            bundle_doc_accepted.item_name = item.item_name
            bundle_doc_accepted.company = default_company
            bundle_doc_accepted.warehouse = self.accepted_warehouse
            bundle_doc_accepted.type_of_transaction = "Inward"
            bundle_doc_accepted.voucher_type = "Bill Of Landing"
            bundle_doc_accepted.voucher_no = self.name
            bundle_doc_accepted.total_qty = flt(item.accepted_qty)
            bundle_doc_accepted.custom_is_active =1
            bundle_doc_accepted.custom_customer = self.customer

            valuation_rate = frappe.db.get_value("Item", item.item_code, "valuation_rate") or 0

            # Populate Serial and Batch Table for Accepted Quantity
            serial_nos_accepted = item.serial_no.split("\n") if item.serial_no else []
            for serial_no in serial_nos_accepted:
                bundle_doc_accepted.append("entries", {
                    "serial_no": serial_no,
                    "batch_no": item.batch_no or "",
                    "qty": 1,
                    "warehouse": self.accepted_warehouse,
                    "valuation_rate": valuation_rate
                })

            bundle_doc_accepted.flags.ignore_mandatory = True
            bundle_doc_accepted.flags.ignore_validate = True
            bundle_doc_accepted.flags.ignore_permissions = True
            bundle_doc_accepted.insert()
            bundle_doc_accepted.submit()

            item.customer_batch_bundle = bundle_doc_accepted.name

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








def time_threshold(self):
    now = datetime.now()
    now_time = now.time()  
    cutoff_start = datetime.strptime(str(self.cutoff_start_time), "%H:%M:%S").time()
    cutoff_end = datetime.strptime(str(self.cutoff_end_time), "%H:%M:%S").time()


    today_name = calendar.day_name[now.weekday()] 
    weekdays_off = [row.weekday for row in self.weekdays_off]  
    if cutoff_start <= now_time <= cutoff_end and today_name not in weekdays_off:
        self.availability_threshold = 0
        self.submitted_between_available_threshold = 1
        return  

   
    today_index = now.weekday()  # Monday = 0, Sunday = 6
    all_days = list(calendar.day_name)

    # Find the next available working day
    for i in range(1, 8):  # Check the next 7 days
        next_day_index = (today_index + i) % 7
        next_day_name = all_days[next_day_index]

        if next_day_name not in weekdays_off:
            next_available_day = now + timedelta(days=i)
            next_cutoff_time = datetime.combine(next_available_day.date(), cutoff_start)
            minutes_diff = (next_cutoff_time - now).total_seconds() / 60


            self.availability_threshold = int(minutes_diff)
            self.submitted_between_available_threshold = 0
            return 


