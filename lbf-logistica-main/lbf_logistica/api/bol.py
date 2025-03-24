import frappe
from frappe import _
import json

# @frappe.whitelist(allow_guest=True) 
# def get_bill_of_landing(customer):
#     if not frappe.session.user or frappe.session.user == "Guest":
#         frappe.throw(_("You are not authorized to access this resource"), frappe.PermissionError)

#     if not customer:
#         frappe.throw(_("Customer is required"))

#     # Fetch filtered records
#     records = frappe.get_all(
#         "Bill Of Landing",
#         filters={"customer": customer},
#         fields=[
#             "name", "customer", "customer_address", "customer_shipping_address",
#             "posting_date", "total_qty", "total_qty_accepted", "total_qty_rejected",
#             "transporter_name", "reference_material_request", "reference_shipment_id",
#             "shipping_to", "shipping_address", "service"
#         ]
#     )

#     # Process each record to add child table data
#     for record in records:
#         # Determine which child table to fetch based on `service`
#         if record.get("service") == "Peneus Hub":
#             record["items"] = frappe.get_all(
#                 "Bill Of Landing Item",
#                 filters={"parent": record["name"]},
#                 fields=["item_code", "item_name", "total_qty","accepted_qty","rejected_qty","serial_and_batch_bundle_accepted","serial_and_batch_bundle_rejected","quality_inspection_done","quality_inspection","serial_no"]
#             )
#         elif record.get("service") == "Tyer Hotel":
#             record["items"] = frappe.get_all(
#                 "Bill of Landing Items TH",
#                 filters={"parent": record["name"]},
#                 fields=["item_code", "item_name", "qty","tyre_type","accepted_qty","rejected_qty","serial_and_batch_bundle_accepted","serial_and_batch_bundle_rejected","quality_inspection_done","quality_inspection","serial_no"]
#             )
#         else:
#             record["items"] = [] 

#     return records


@frappe.whitelist(allow_guest=False)
def get_bill_of_landing():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(_("You are not authorized to access this resource"), frappe.PermissionError)
    
    customer = frappe.db.get_value("Portal User", {"user": frappe.session.user}, "parent")
    
    if not customer:
        frappe.throw(_("No customer is associated with this user"), frappe.PermissionError)
    
    records = frappe.get_all(
        "Bill Of Landing",
        filters={"customer": customer, "legal_doc_for_redelivery": 0},
        fields=[
            "name", "customer", "party_type", "service", "accepted_warehouse",
            "posting_date", "total_qty", "total_qty_accepted", "total_qty_rejected", "total_qty_th", "total_tyres_with_rim", "total_tyres_without_rim",
            "reference_material_request", "reference_shipment_id", "customer_address", "address",
            "customer_contact", "contact", "shipping_to", "customer_shipping_address", "shipping_address",
            "transporter_name", "transporter_address", "transporter_contact", "transport_contact", "docstatus", "status", "legal_doc_for_redelivery",
        ]
    )
    
    for record in records:
        item_doctype = "Bill Of Landing Item" if record.get("service") == "Peneus Hub" else "Bill of Landing Items TH" if record.get("service") == "Tyre Hotel" else None
        
        if item_doctype:
            fields = [
                "item_code", "item_name", 
                "total_qty" if item_doctype == "Bill Of Landing Item" else "qty",
                "tyre_type" if item_doctype == "Bill of Landing Items TH" else None,
                "accepted_qty", "rejected_qty", "serial_and_batch_bundle_accepted",
                "serial_and_batch_bundle_rejected"
            ]
            
            # Add the correct quality inspection field based on the service type
            if record.get("service") == "Tyre Hotel":
                fields.append("done_quality_inspection")
                fields.append("quality_inspection")
            else:
                fields.append("quality_inspection_done")
                fields.append("quality_inspection")
            
            fields.append("serial_no")
            
            items = frappe.get_all(
                item_doctype,
                filters={"parent": record["name"]},
                fields=fields
            )
            
            for item in items:
                if item.get("serial_and_batch_bundle_accepted"):
                    item["serial_and_batch_bundle_accepted_data"] = frappe.get_doc("Serial and Batch Bundle", item["serial_and_batch_bundle_accepted"])
                
                # Check the correct quality inspection field based on the service type
                quality_inspection_field = "done_quality_inspection" if record.get("service") == "Tyre Hotel" else "quality_inspection_done"
                
                if item.get(quality_inspection_field) and item.get("quality_inspection"):
                    item["quality_inspection_data"] = frappe.get_doc("Quality Inspection", item["quality_inspection"])
            
            record["items"] = items
        else:
            record["items"] = []

        if record.get("service") == "Peneus Hub":
            handling_in_charges = frappe.get_all(
                "Handling In Charges",
                filters={"parent": record["name"]},
                fields=["item_code", "item_name", "accepted_qty", "amount", "rate"]
            )
            record["handling_in_charges"] = handling_in_charges

    return records





# @frappe.whitelist(allow_guest=True)
# def save_material_request_instruction_log():
#     try:
#         data = frappe.request.get_json()
#         if not data:
#             return {
#                 "code": 400,
#                 "message": "Bad request",
#                 "error": "Request data is required"
#             }
#         if data.get("service") == "Peneus Hub":
#             ml_data = frappe.get_doc({
#                 "doctype": "Material Request Instruction Log",
#                 "service": data.get("service"),
#                 "material_request_type": data.get("material_request_type"),
#                 "schedule_date": str(data.get("schedule_date")),
#                 # "posting_time": data.get("posting_time"),
#                 # "transaction_date": data.get("transaction_date"),
#                 "party_type": data.get("party_type"),
#                 "customer": data.get("customer"),
#                 "address_of_customer": data.get("address_of_customer"),
#                 "shipping_to":data.get("shipping_to"),
#                 "shipping_address_name":data.get("shipping_address_name"),
#                 "address":data.get("address"),
#                 "customer_contact":data.get("customer_contact"),
#                 "contact_person":data.get("contact_person"),
#                 "contact":data.get("contact"),
#                 "transporter_name": data.get("transporter_name"),
#                 "transporter_address": data.get("transporter_address"),
#                 "items": []
#                 })  
     
#             if  "items" in data and isinstance(data["items"], list):
#                 for item in data["items"]:
#                     ml_data.append("items", {
#                         "item_code": item.get("item_code"),
#                         "item_name": item.get("item_name"),
#                         "schedule_date": str(item.get("schedule_date")),
#                         "qty": item.get("qty"),
#                         "uom": item.get("uom"),
#                         "uom_qty": item.get("uom_qty"),
#                         "conversion_factor": item.get("conversion_factor"),
#                         "warehouse": item.get("warehouse"),
#                         "description": item.get("description")

#                     })

#         if data.get("service") == "Tyre Hotel":
#             ml_data = frappe.get_doc({
#                 "doctype": "Material Request Instruction Log",
#                 "service": data.get("service"),
#                 "material_request_type": data.get("material_request_type"),
#                 "schedule_date": str(data.get("schedule_date")),
#                 # "posting_time": data.get("posting_time"),
#                 # "transaction_date": data.get("transaction_date"),
#                 "party_type": data.get("party_type"),
#                 "customer": data.get("customer"),
#                 "address_of_customer": data.get("address_of_customer"),
#                 "shipping_to":data.get("shipping_to"),
#                 "shipping_address_name":data.get("shipping_address_name"),
#                 "address":data.get("address"),
#                 "customer_contact":data.get("customer_contact"),
#                 "contact_person":data.get("contact_person"),
#                 "contact":data.get("contact"),
#                 "transporter_name": data.get("transporter_name"),
#                 "transporter_address": data.get("transporter_address"),
#                 "season": data.get("season"),
#                 "license_plate": data.get("license_plate"),
#                 "mezzo": data.get("mezzo"),
#                 "condition": data.get("condition"),
#                 "reason": data.get("reason"),
#                 "items": []
#                 }) 
#             if  "items" in data and isinstance(data["items"], list):
#                 for item in data["items"]:
#                     ml_data.append("th_items", {
#                         "item_code": item.get("item_code"),
#                         "item_name": item.get("item_name"),
#                         "schedule_date": item.get("schedule_date"),
#                         "qty": item.get("qty"),
#                         "type": item.get("type"),
#                         "uom": item.get("uom"),
#                         "uom_qty": item.get("uom_qty"),
#                         "conversion_factor": item.get("conversion_factor"),
#                         "warehouse": item.get("warehouse"),
#                         "description": item.get("description")

#                     })
#         try:
            
#             ml_data.save(ignore_permissions=True)
#             frappe.db.commit()      
#             return {
#                     "code": 200,
#                     "message": "Data saved successfully",
#                     "name": ml_data.name 
#                 }
#         except Exception as e:
#             print(e)
#             frappe.log_error(frappe.get_traceback(), _("Material Request Instruction Log Creation Failed"))
#             frappe.log_error(e)
#             return {
#                 "code": 500,
#                 "message": "Internal server error",
#                 "error": str(e),
#             }
#     except Exception as e:
#         print(e)
#         return {
#             "code": 500,
#             "message": "Internal server error",
#             "error": str(e),
#         }


@frappe.whitelist(allow_guest=True)
def save_material_request_instruction_log():
    try:
        data = frappe.request.get_json()
        if not data:
            return {
                "code": 400,
                "message": "Bad request",
                "error": "Request data is required"
            }

        # Check if "name" is provided in the payload for update
        if data.get("name"):
            try:
                ml_data = frappe.get_doc("Material Request Instruction Log", data.get("name"))
                is_update = True
            except frappe.DoesNotExistError:
                return {
                    "code": 404,
                    "message": "Record not found",
                    "error": f"No record found with name {data.get('name')}"
                }
        else:
            is_update = False
            ml_data = frappe.get_doc({"doctype": "Material Request Instruction Log"})

        # Common fields for both update and create
        
        ml_data.update({
            "service": data.get("service"),
            "material_request_type": data.get("material_request_type"),
            "schedule_date": str(data.get("schedule_date")),
            "party_type": data.get("party_type"),
            "customer": data.get("customer"),
            # "address_of_customer": data.get("address_of_customer"),
            "shipping_to": data.get("shipping_to"),
            "shipping_address_name": data.get("shipping_address_name"),
            "customer_contact": data.get("customer_contact"),
            "contact_person": data.get("contact_person"),
            "contact": data.get("contact"),
            "email": data.get("email"),
            "transporter_name": data.get("transporter_name"),
            # "transporter_address": data.get("transporter_address"),
            # "posting_time": data.get("posting_time"),
            # "transaction_date": data.get("transaction_date"),
        })

        # If service is "Tyre Hotel", add specific fields
        if data.get("service") == "Tyre Hotel":
            ml_data.update({
                "season": data.get("season"),
                "license_plate": data.get("license_plate"),
                "mezzo": data.get("mezzo"),
                "condition": data.get("condition"),
                "reason": data.get("reason"),
            })

        # If updating, clear existing child table before appending new data
        if is_update:
            ml_data.set("items", [])  
            ml_data.set("th_items", [])

        # Handle items child table
        if "items" in data and isinstance(data["items"], list):
            for item in data["items"]:
                child_table = "th_items" if data.get("service") == "Tyre Hotel" else "items"
                
                item_data = {
                    "item_code": item.get("item_code"),
                    "item_name": item.get("item_name"),
                    "schedule_date": str(item.get("schedule_date")),
                   "qty": int(item.get("qty", 0)) if isinstance(item.get("qty", ""), str) and item.get("qty", "").isdigit() else int(item.get("qty", 0) or 0),
                    "uom": item.get("uom"),
                    "uom_qty": item.get("uom_qty"),
                    "conversion_factor": item.get("conversion_factor"),
                    "warehouse": item.get("warehouse"),
                    "description": item.get("description"),
                    "type": item.get("type") if data.get("service") == "Tyre Hotel" else None
                }

                # If service is "Tyre Hotel" and purpose is "Redelivery", fetch additional fields from Item
                if data.get("service") == "Tyre Hotel" and data.get("material_request_type") == "Redelivery" and item.get("item_code"):
                    try:
                        item_doc = frappe.get_doc("Item", item.get("item_code")) 

                    # Mapping of expected field names to actual field names in the Item doctype
                        field_mapping = {
                            "aspect_ratio": "custom_aspect_ratio",
                            "brand": "brand",  
                            "carcass": "custom_carcass",
                            "diameterinch": "custom_diameterinch",
                            "load_index": "custom_load_index",
                            "marks": "custom_marks",
                            "model": "custom_model",
                            "speed_rating": "custom_speed_rating",
                            "tire_widthmm": "custom_tire_widthmm",
                            "weight": "custom_weight",
                        }

                        for target_field, item_field in field_mapping.items():
                            if hasattr(item_doc, item_field) and item_doc.get(item_field):
                                item_data[target_field] = item_doc.get(item_field)
                    except frappe.DoesNotExistError:
                        pass

                
                # If service is "Tyre Hotel" and purpose is "Pick up" with item "Others"
                if data.get("service") == "Tyre Hotel" and data.get("material_request_type") == "Pick Up" and item.get("item_code") == "Others":
                    item_data.update({
                        "other_item_code": item.get("other_item_code"),
                        "other_item_name": item.get("other_item_name"),
                        "aspect_ratio_others": item.get("aspect_ratio_others"),
                        "brandothers": item.get("brandothers"),
                        "carcass_others": item.get("carcass_others"),
                        "diameterinch_others": item.get("diameterinch_others"),
                        "load_index_others": item.get("load_index_others"),
                        "marks_others": item.get("marks_others"),
                        "model_others": item.get("model_others"),
                        "speed_rating_others": item.get("speed_rating_others"),
                        "tire_widthmm_others": item.get("tire_widthmm_others"),
                        "weight_others": item.get("weight_others"),
                    })

                ml_data.append(child_table, item_data)



        # Fetch the total address on the basis of the shipping address name
        if data.get("shipping_address_name"):
            address_doc = frappe.get_doc("Address", data.get("shipping_address_name"))
            
            formatted_address = f"""{address_doc.address_title or ''} · {address_doc.address_type or ''}
{address_doc.address_line1 or ''}
{address_doc.city or ''}, {address_doc.state or ''}
PIN Code: {address_doc.pincode or ''}
{address_doc.country or ''}
            """

            ml_data.update({"address": formatted_address})
            
        # Fetch the transporter's address
        if data.get("transporter_name"):
            transporter_address = frappe.db.sql("""
                SELECT
                    addr.address_title, addr.address_type, addr.address_line1, addr.city, addr.state, addr.pincode, addr.country
                FROM
                    `tabAddress` addr
                JOIN
                    `tabDynamic Link` links ON links.parent = addr.name
                WHERE
                    links.link_name = %s AND links.link_doctype = 'Supplier'
                LIMIT 1
            """, (data.get("transporter_name"),), as_dict=True)

            if transporter_address:
                        addr = transporter_address[0]
                        formatted_transporter_address = f"""{addr.get('address_title', '')} · {addr.get('address_type', '')}
{addr.get('address_line1', '')} 
{addr.get('city', '')}, {addr.get('state', '')}  
PIN Code: {addr.get('pincode', '')} 
{addr.get('country', '')}
                        """
            else:
                formatted_transporter_address = "No address found"

            ml_data.update({"transporter_address": formatted_transporter_address})

        
        # Fetch transporter's weekdays off
        if data.get("transporter_name"):
            supplier_doc = frappe.get_doc("Supplier", data.get("transporter_name"))

            if hasattr(supplier_doc, "custom_weekdays_off") and supplier_doc.custom_weekdays_off:
                ml_data.set("weekdays_off", [])  # Clear existing records before adding new ones

                for weekday in supplier_doc.custom_weekdays_off:
                    row = ml_data.append("weekdays_off", {})

                    for field in weekday.as_dict():
                        if field not in ['name', 'owner', 'creation', 'modified', 'modified_by', 'parent', 'parentfield', 'parenttype', 'idx']:
                            row.set(field, weekday.get(field))




       # Fetch the customer's address 
        if data.get("customer"):
            customer_address = frappe.db.sql("""
                SELECT
                    addr.address_title, addr.address_type, addr.address_line1, addr.city, addr.state, addr.pincode, addr.country
                FROM
                    `tabAddress` addr
                JOIN
                    `tabDynamic Link` links ON links.parent = addr.name
                WHERE
                    links.link_name = %s AND links.link_doctype = 'Customer'
                LIMIT 1
            """, (data.get("customer"),), as_dict=True)

            if customer_address:
                addr = customer_address[0]
                formatted_customer_address = f"""{addr.get('address_title', '')} · {addr.get('address_type', '')}
{addr.get('address_line1', '')} 
{addr.get('city', '')}, {addr.get('state', '')}  
PIN Code: {addr.get('pincode', '')} 
{addr.get('country', '')}
                """
            else:
                formatted_customer_address = "No address found"

            ml_data.update({"address_of_customer": formatted_customer_address})


        try:
            ml_data.save(ignore_permissions=True)
            frappe.db.commit()
            return {
                "code": 200,
                "message": "Material Request Instruction Log updated successfully" if is_update else "Material Request Instruction Log saved successfully",
                "name": ml_data.name
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), _("Material Request Instruction Log Save Failed"))
            return {
                "code": 500,
                "message": "Internal server error",
                "error": str(e),
            }
    except Exception as e:
        return {
            "code": 500,
            "message": "Internal server error",
            "error": str(e),
        }




@frappe.whitelist(allow_guest=True)
def get_customer_contacts(customer_name):
    # if not frappe.has_permission("Contact", "read"):
    #     frappe.throw("Not permitted", frappe.PermissionError)

    contacts = frappe.db.get_all("Contact", 
        filters={"name": ["in", frappe.db.get_all("Dynamic Link", filters={
            "link_name": customer_name, "parenttype": "Contact"
        }, pluck="parent")]}, 
        fields=["name","links.link_name", "email_id","email_ids.email_id","phone_nos.phone"]
    )
    return contacts







@frappe.whitelist(allow_guest=True)
def get_unique_items(customer, fields=None):
    try:
        if not fields:
            fields = ["item_code"]
        else:
            try:
                fields = json.loads(fields)
                if not isinstance(fields, list):
                    frappe.throw("Fields parameter should be a list.")
            except json.JSONDecodeError:
                frappe.throw('Invalid fields format. It should be a JSON array like ["item_code", "serial_no"].')

        meta = frappe.get_meta("Serial No")

        all_valid_fields = [
            df.fieldname for df in meta.fields
            if not df.fieldname.startswith('_')
            and df.fieldname in frappe.db.get_table_columns("Serial No")
        ]

        frappe.logger().debug(f"All valid fields: {all_valid_fields}")

        if "*" in fields:
            valid_fields = all_valid_fields
        else:
            valid_fields = [field for field in fields if field in all_valid_fields]

        if not valid_fields:
            frappe.throw("No valid fields provided.")

        frappe.logger().debug(f"Selected valid fields: {valid_fields}")

        invalid_fields = [field for field in fields if field not in all_valid_fields and field != "*"]
        if invalid_fields:
            frappe.log_error(
                f"Invalid fields requested: {invalid_fields}",
                "get_unique_items API Error"
            )

    
        query = f"""
            SELECT {", ".join(valid_fields)}, COUNT(sn.name) AS actual_qty
            FROM `tabSerial No` sn
            WHERE sn.custom_customer = %s 
              AND sn.status = 'Active' 
              AND sn.custom_type_of_warehouse = 'Location'
              AND sn.custom_tyre_type = ''
              AND sn.custom_service = 'Peneus Hub'
            GROUP BY {", ".join(valid_fields)}
        """

        frappe.logger().debug(f"Query: {query}")

        items = frappe.db.sql(query, (customer,), as_dict=True)

        return items

    except Exception as e:
        frappe.log_error(
            message=f"Error in get_unique_items: {str(e)}\nQuery: {query if 'query' in locals() else 'Query not constructed'}\nFields: {fields}",
            title="get_unique_items API Error"
        )
        frappe.throw("An error occurred while fetching items. Please try again or contact support.")

@frappe.whitelist(allow_guest=True)
def get_customers_with_parent(customer_name):
    if not customer_name:
        frappe.response["data"] = []
        return
    
    child_customers = frappe.get_all(
        "Child Customer",
        filters={"parent": customer_name},
        fields=["customer"]
    )

    customers = [{"name":d["customer"]} for d in child_customers]
    customers.append({"name":customer_name} ) 


  

    frappe.response["data"] = customers







@frappe.whitelist(allow_guest=True)
def submit_material_request(name):
    try:
        # Check if document exists
        if not frappe.db.exists("Material Request Instruction Log", name):
            return {"status": "error", "message": f"No record found with name {name}", "docstatus": None}

        doc = frappe.get_doc("Material Request Instruction Log", name)

        # Capture the current docstatus before attempting to submit
        current_docstatus = doc.docstatus

        # Ensure the document is not already submitted
        if current_docstatus == 0:
            doc.submit()
            return {
                "status": "success",
                "message": f"Document {name} submitted successfully",
                "docstatus": 1  # Since it will be submitted now
            }
        else:
            return {
                "status": "error",
                "message": f"Document {name} is already submitted",
                "docstatus": current_docstatus
            }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Material Request Submission Error"))
        return {"status": "error", "message": str(e), "docstatus": None}


@frappe.whitelist(allow_guest=True)
def create_customer():
    data = frappe.request.get_json()
    """
    API endpoint to create a new customer with address and contact details
    
    Args:
        data (dict): JSON data containing customer information
            {
                "customer_name": "Required",
                "customer_type": "Company/Individual",
                "customer_group": "Required",
                "territory": "Required",
                "addresses": [
                    {
                        "address_title": "Required",
                        "address_line1": "Required",
                        "city": "Required",
                        "country": "Required",
                        "is_primary_address": 0/1,
                        "is_shipping_address": 0/1,
                        "pincode": "Optional"
                        // other address fields
                    }
                ],
                "contacts": [
                    {
                        "first_name": "Required",
                        "last_name": "Optional",
                        "email_id": "Optional",
                        "phone": "Optional",
                        "is_primary_contact": 0/1
                        // other contact fields
                    }
                ]
            }
    
    Returns:
        dict: JSON response with customer details or error message
    """
    try:
        # Validate required fields
        if not data.get("customer_name"):
            return {"success": False, "message": "Customer name is required"}
            
        if not data.get("customer_group"):
            return {"success": False, "message": "Customer group is required"}

        if not data.get("mail_id") and not data.get("contact_no"):
            return {"success": False, "message": "Mail id or Contact no is required"}


        mail_id = data.get("mail_id") or None
        contact_no = data.get("contact_no") or None

        existing_customer = None

        if mail_id or contact_no:
            existing_customer_doc = frappe.db.get_value(
                "Customer",
                {"custom_mail_id": mail_id} if mail_id else {"custom_contact_no": contact_no},
                "name"
            )

            if existing_customer_doc:
                existing_customer = frappe.get_doc("Customer", existing_customer_doc)
            else:
                existing_customer = None




        if existing_customer:



            addresses = []
            primary_address = None
            if data.get("addresses"):
                for addr_data in data.get("addresses"):
                    if not addr_data.get("address_title"):
                        continue
                            
                    if not addr_data.get("address_line1"):
                        continue
                            
                    address = frappe.get_doc({
                        "doctype": "Address",
                        "address_title": addr_data.get("address_title"),
                        "address_line1": addr_data.get("address_line1"),
                        "address_line2": addr_data.get("address_line2", ""),
                        "city": addr_data.get("city", ""),
                        "state": addr_data.get("state", ""),
                        "pincode": addr_data.get("pincode", ""),
                        "country": addr_data.get("country", ""),
                        "is_primary_address": addr_data.get("is_primary_address", 0),
                        "is_shipping_address": addr_data.get("is_shipping_address", 0),
                        "links": [{
                            "link_doctype": "Customer",
                            "link_name": existing_customer.name
                        }]
                    })
                    if addr_data.get("custom_transporters"):
                        for transporter in addr_data.get("custom_transporters"):
                            address.append("custom_transporters", {
                                "supplier": transporter.get("supplier"),
                                "is_default": transporter.get("is_default")
                            })
                
                    
                    address.insert(ignore_permissions=True)
                    addresses.append(address.name)
                    
                    # Track primary address
                    if addr_data.get("is_primary_address", 0) == 1:
                        primary_address = address.name

            # Handle contacts
            contacts = []
            primary_contact = None
            if data.get("contacts"):
                for contact_data in data.get("contacts"):
                    if not contact_data.get("first_name"):
                        continue
                            
                    contact = frappe.get_doc({
                        "doctype": "Contact",
                        "first_name": contact_data.get("first_name"),
                        "last_name": contact_data.get("last_name", ""),
                        "email_id": contact_data.get("email_id", ""),
                        "phone": contact_data.get("phone", ""),
                        "is_primary_contact": contact_data.get("is_primary_contact", 0),
                        "links": [{
                            "link_doctype": "Customer",
                            "link_name": existing_customer.name
                        }]
                    })
                    
                    # Add email addresses
                    if contact_data.get("email_id"):
                        contact.append("email_ids", {
                            "email_id": contact_data.get("email_id"),
                            "is_primary": 1
                        })
                    
                    # Add phone numbers
                    if contact_data.get("phone"):
                        contact.append("phone_nos", {
                            "phone": contact_data.get("phone"),
                            "is_primary_phone": 1
                        })
                            
                    contact.insert(ignore_permissions=True)
                    contacts.append(contact.name)
                    
                    # Track primary contact
                    if contact_data.get("is_primary_contact", 0) == 1:
                        primary_contact = contact.name
            

            main_customer_id = frappe.session.user

            # Find Customers where portal_users.user matches main_customer_id
            linked_customers = frappe.db.sql("""
                SELECT DISTINCT parent 
                FROM `tabPortal User` 
                WHERE user = %s
            """, (main_customer_id,), as_dict=True)

            if linked_customers:
                for cust in linked_customers:
                    linked_customer_doc = frappe.get_doc("Customer", cust["parent"])
                    existing_customer.append("custom_details_for_parent_customer", {
                        "parent_customer": linked_customer_doc.name, 
                        "child_customer_name": data.get("customer_name"),
                        "child_customer_address_name": address.name if address else None,
                        "child_customer_contact_name": contact.name if contact else None
                    })

            # Set primary address and contact on customer if available
            if addresses:
                # If no primary address was explicitly set but addresses exist, use the first one as primary
                if not primary_address:
                    primary_address = addresses[0]
                
                # Update customer's primary address
                existing_customer.customer_primary_address = primary_address

            if contacts:
                # If no primary contact was explicitly set but contacts exist, use the first one as primary
                if not primary_contact:
                    primary_contact = contacts[0]
                
                # Update customer's primary contact
                existing_customer.customer_primary_contact = primary_contact

            # Save the customer to update primary address and contact
            existing_customer.save(ignore_permissions=True)

            # Commit transaction
            # frappe.db.commit()

            main_customer_id = frappe.session.user

            # Find Customers where portal_users.user matches main_customer_id
            linked_customers = frappe.db.sql("""
                SELECT DISTINCT parent 
                FROM `tabPortal User` 
                WHERE user = %s
            """, (main_customer_id,), as_dict=True)

            # Update custom_child_customer in those customers
            for linked_customer in linked_customers:
                linked_customer_doc = frappe.get_doc("Customer", linked_customer["parent"])
                linked_customer_doc.append("custom_child_customer", {
                    "customer": existing_customer.name
                })
                linked_customer_doc.save(ignore_permissions=True)

            frappe.db.commit()



        else:

            
            # Create customer
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": data.get("customer_name"),
                "customer_type": data.get("customer_type") or "Company",
                "customer_group": data.get("customer_group"),
                "territory": data.get("territory"),
                "default_currency": data.get("default_currency") or "EUR",
                "custom_mail_id": mail_id or None,
                "custom_contact_no": contact_no or None
            })
            
            customer.insert(ignore_permissions=True)
            
            # Handle addresses
            addresses = []
            primary_address = None
            if data.get("addresses"):
                for addr_data in data.get("addresses"):
                    if not addr_data.get("address_title"):
                        continue
                            
                    if not addr_data.get("address_line1"):
                        continue
                            
                    address = frappe.get_doc({
                        "doctype": "Address",
                        "address_title": addr_data.get("address_title"),
                        "address_line1": addr_data.get("address_line1"),
                        "address_line2": addr_data.get("address_line2", ""),
                        "city": addr_data.get("city", ""),
                        "state": addr_data.get("state", ""),
                        "pincode": addr_data.get("pincode", ""),
                        "country": addr_data.get("country", ""),
                        "is_primary_address": addr_data.get("is_primary_address", 0),
                        "is_shipping_address": addr_data.get("is_shipping_address", 0),
                        "links": [{
                            "link_doctype": "Customer",
                            "link_name": customer.name
                        }]
                    })
                    if addr_data.get("custom_transporters"):
                        for transporter in addr_data.get("custom_transporters"):
                            address.append("custom_transporters", {
                                "supplier": transporter.get("supplier"),
                                "is_default": transporter.get("is_default")
                            })
                
                    
                    address.insert(ignore_permissions=True)
                    addresses.append(address.name)
                    
                    # Track primary address
                    if addr_data.get("is_primary_address", 0) == 1:
                        primary_address = address.name

            # Handle contacts
            contacts = []
            primary_contact = None
            if data.get("contacts"):
                for contact_data in data.get("contacts"):
                    if not contact_data.get("first_name"):
                        continue
                            
                    contact = frappe.get_doc({
                        "doctype": "Contact",
                        "first_name": contact_data.get("first_name"),
                        "last_name": contact_data.get("last_name", ""),
                        "email_id": contact_data.get("email_id", ""),
                        "phone": contact_data.get("phone", ""),
                        "is_primary_contact": contact_data.get("is_primary_contact", 0),
                        "links": [{
                            "link_doctype": "Customer",
                            "link_name": customer.name
                        }]
                    })
                    
                    # Add email addresses
                    if contact_data.get("email_id"):
                        contact.append("email_ids", {
                            "email_id": contact_data.get("email_id"),
                            "is_primary": 1
                        })
                    
                    # Add phone numbers
                    if contact_data.get("phone"):
                        contact.append("phone_nos", {
                            "phone": contact_data.get("phone"),
                            "is_primary_phone": 1
                        })
                            
                    contact.insert(ignore_permissions=True)
                    contacts.append(contact.name)
                    
                    # Track primary contact
                    if contact_data.get("is_primary_contact", 0) == 1:
                        primary_contact = contact.name


            main_customer_id = frappe.session.user

            # Find Customers where portal_users.user matches main_customer_id
            linked_customers = frappe.db.sql("""
                SELECT DISTINCT parent 
                FROM `tabPortal User` 
                WHERE user = %s
            """, (main_customer_id,), as_dict=True)

            if linked_customers:
                for cust in linked_customers:
                    linked_customer_doc = frappe.get_doc("Customer", cust["parent"])
                    customer.append("custom_details_for_parent_customer", {
                        "parent_customer": linked_customer_doc.name, 
                        "child_customer_name": data.get("customer_name"),
                        "child_customer_address_name": address.name if address else None,
                        "child_customer_contact_name": contact.name if contact else None
                    })
            # Set primary address and contact on customer if available
            if addresses:
                # If no primary address was explicitly set but addresses exist, use the first one as primary
                if not primary_address:
                    primary_address = addresses[0]
                
                # Update customer's primary address
                customer.customer_primary_address = primary_address

            if contacts:
                # If no primary contact was explicitly set but contacts exist, use the first one as primary
                if not primary_contact:
                    primary_contact = contacts[0]
                
                # Update customer's primary contact
                customer.customer_primary_contact = primary_contact

            # Save the customer to update primary address and contact
            customer.save(ignore_permissions=True)

            # Commit transaction
            # frappe.db.commit()

            main_customer_id = frappe.session.user

            # Find Customers where portal_users.user matches main_customer_id
            linked_customers = frappe.db.sql("""
                SELECT DISTINCT parent 
                FROM `tabPortal User` 
                WHERE user = %s
            """, (main_customer_id,), as_dict=True)

            # Update custom_child_customer in those customers
            for linked_customer in linked_customers:
                linked_customer_doc = frappe.get_doc("Customer", linked_customer["parent"])
                linked_customer_doc.append("custom_child_customer", {
                    "customer": customer.name
                })
                linked_customer_doc.save(ignore_permissions=True)

            frappe.db.commit()

        

        return {
            "success": True,
            "message": "Customer created successfully",
            "customer": customer.name,
            "addresses": addresses,
            "contacts": contacts
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Customer API Error")
        return {"success": False, "message": str(e)}
    




@frappe.whitelist(allow_guest=True)
def get_unique_tyre_hotel_items(customer, custom_tyre_type=None, fields=None, license_plate=None):
    try:
        if not fields:
            fields = ["item_code"]
        else:
            try:
                fields = json.loads(fields)
                if not isinstance(fields, list):
                    frappe.throw("Fields parameter should be a list.")
            except json.JSONDecodeError:
                frappe.throw('Invalid fields format. It should be a JSON array like ["item_code", "serial_no"].')

        meta = frappe.get_meta("Serial No")

        all_valid_fields = [
            df.fieldname for df in meta.fields
            if not df.fieldname.startswith('_')
            and df.fieldname in frappe.db.get_table_columns("Serial No")
        ]

        if "*" in fields:
            valid_fields = all_valid_fields
        else:
            valid_fields = [field for field in fields if field in all_valid_fields]

        if not valid_fields:
            frappe.throw("No valid fields provided.")

        invalid_fields = [field for field in fields if field not in all_valid_fields and field != "*"]
        if invalid_fields:
            frappe.log_error(
                f"Invalid fields requested: {invalid_fields}",
                "get_unique_tyre_hotel_items API Error"
            )

        # Base query with required filters
        query = f"""
            SELECT {", ".join(valid_fields)}, COUNT(sn.name) AS actual_qty
            FROM `tabSerial No` sn
            WHERE sn.custom_customer = %s
              AND sn.status = 'Active'
              AND sn.custom_type_of_warehouse = 'Location'
              AND sn.custom_service = 'Tyre Hotel'
        """

        values = [customer]

        # If custom_tyre_type is provided, add it to the query
        if custom_tyre_type:
            query += " AND sn.custom_tyre_type = %s"
            values.append(custom_tyre_type)


        if license_plate:
            query += " AND sn.custom_license_plate = %s"
            values.append(license_plate)

        query += f" GROUP BY {', '.join(valid_fields)}"

        frappe.logger().debug(f"Query: {query}")

        items = frappe.db.sql(query, tuple(values), as_dict=True)

        return items
    
    except Exception as e:
        frappe.log_error(
            message=f"Error in get_unique_items: {str(e)}\nQuery: {query if 'query' in locals() else 'Query not constructed'}\nFields: {fields}",
            title="get_unique_items API Error"
        )
        frappe.throw("An error occurred while fetching items. Please try again or contact support.")






@frappe.whitelist(allow_guest=True)
def fetch_child_customers(customer):
    try:

        customer_doc = frappe.get_doc("Customer", customer)

        child_customers = []
        for child in customer_doc.custom_child_customer:
            child_customer_doc = frappe.get_doc("Customer", child.customer)
            child_customers.append(child_customer_doc.name)

        child_customer_set = set(child_customers)

        child_customers_list = []
        for c in child_customer_set:
            child_customer_data = frappe.get_doc("Customer", c)
            child_customers_list.append(child_customer_data.as_dict())

        

        
        return  child_customers_list
        
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Fetch Child Customers Error")
        return {"success": False, "message": str(e)}





@frappe.whitelist(allow_guest=False)
def get_customer_group():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.throw(_("You are not authorized to access this resource"), frappe.PermissionError)
    
    customer_group = frappe.get_all("Customer Group")
    return customer_group    
   