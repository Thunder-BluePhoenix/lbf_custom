import frappe
from frappe.model.document import Document


def before_save_item(doc, method):

    if doc.get("__islocal") or doc.item_code: 
        doc.has_batch_no = 1
        doc.has_serial_no = 1
        doc.create_new_batch = 1


        doc.batch_number_series = doc.batch_number_series or "BN.########"
        doc.serial_no_series = doc.serial_no_series or "SN.########"




def add_titolo(doc, method):
    if doc.custom_tire_widthmm and doc.custom_aspect_ratio and doc.custom_diameterinch:
        # Collect field values

        tire_width = doc.custom_tire_widthmm or ''  # Replace with your custom field name
        aspect_ratio = doc.custom_aspect_ratio or ''  # Replace with your custom field name
        carcass = doc.custom_carcass or ''  # Replace with your custom field name
        diameter = doc.custom_diameterinch or ''  # Replace with your custom field name
        load_index = doc.custom_load_index or ''  # Replace with your custom field name
        speed_rating = doc.custom_speed_rating or ''  # Replace with your custom field name
        model = doc.custom_model or ''  # Replace with your custom field name
        marks = doc.custom_marks or ''  # Replace with your custom field name
        brand = doc.brand or ''  # This is the original field
       
        
        

        # Generate tyre name
        tyre_name = f"{tire_width}/{aspect_ratio}{carcass}{diameter} {load_index}{speed_rating} {marks} {brand} {model}"

        # Assign to custom_titolo field
        doc.item_name = tyre_name
        doc.custom_titolo = tyre_name