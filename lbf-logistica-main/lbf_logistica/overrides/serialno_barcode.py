import frappe
import hashlib
import hashlib
import re
import frappe

# @frappe.whitelist()
# def generate_document_barcode(doc):
    
#     if not doc:
#         return None
    
#     unique_string = ""

#     key_fields = [
#         'name',  
#         'item_code', 'custom_service', 'warehouse', 'batch_no', 'custom_posting_time', 'custom_producer_code', 'custom_upc', 'serial_no', 'custom_tire_widthmm', 'custom_aspect_ratio', 
#         'custom_carcass', 'custom_diameterinch', 'custom_load_index', 'custom_speed_rating', 'custom_weight', 'custom_model', 'custom_marks', 'brand', 
#         'custom_customer_name', 'custom_customer_code', 'custom_slug', 'custom_creation_reference_doctype', 'custom_creation_document_name', 
#         'creation',  # Creation timestamp
#     ]
    
   
#     for field in key_fields:
#         value = doc.get(field, '')
#         if value:
#             unique_string += str(value)
    
  
#     barcode_hash = hashlib.md5(unique_string.encode()).hexdigest()
#     numeric_barcode = ''.join(filter(str.isdigit, barcode_hash))[:12]
#     def calculate_check_digit(partial_code):
#         # EAN-13 check digit calculation
#         weights = [1, 3] * 6
#         total = sum(int(partial_code[i]) * weights[i] for i in range(12))
#         check_digit = (10 - (total % 10)) % 10
#         return check_digit
#     full_barcode = numeric_barcode + str(calculate_check_digit(numeric_barcode))
    
#     return full_barcode






@frappe.whitelist()
def generate_document_barcode(doc):
    if not doc:
        return None

    unique_string = ""

    key_fields = [
        'name',  
        'item_code', 'custom_service', 'warehouse', 'batch_no', 'custom_posting_time', 'custom_producer_code', 'custom_upc', 'serial_no', 'custom_tire_widthmm', 'custom_aspect_ratio', 
        'custom_carcass', 'custom_diameterinch', 'custom_load_index', 'custom_speed_rating', 'custom_weight', 'custom_model', 'custom_marks', 'brand', 
        'custom_customer_name', 'custom_customer_code', 'custom_slug', 'custom_creation_reference_doctype', 'custom_creation_document_name', 
        'creation',  # Creation timestamp
    ]

    # Build the unique string
    for field in key_fields:
        value = doc.get(field, '')
        if value:
            unique_string += str(value)

    # Generate a hash of the unique string
    barcode_hash = hashlib.md5(unique_string.encode()).hexdigest()

    # Extract only Code 39 compatible characters: A-Z, 0-9, and -.$%/+.
    compatible_characters = re.sub(r'[^A-Z0-9\-.$%/+ ]', '', barcode_hash.upper())

    # Limit the length (optional, for practical purposes, e.g., 20 characters max)
    barcode_code39 = compatible_characters[:20]

    # Add start and stop characters (*) for Code 39
    full_barcode = f"*{barcode_code39}*"

    return full_barcode

def before_save_serial(doc, method):
    try:
        if not doc.get('custom_barcode'):
            doc.custom_barcode = generate_document_barcode(doc)
    except Exception as e:
        frappe.log_error(f"Barcode Generation Error: {str(e)}")





# def on_update_serialnos(doc, method):
#     warehouse = doc.warehouse
#     warehouse_doc = frappe.get_doc("Warehouse" , warehouse)

#     warehouse_type = warehouse_doc.custom_type_of_warehouse

#     if doc.custom_type_of_warehouse != warehouse_type:
#         doc.custom_type_of_warehouse = warehouse_type
#         doc.save

