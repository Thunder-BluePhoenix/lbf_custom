import frappe

def update_quality_inspection_done(doc, method):
    if doc.reference_type == "Bill Of Landing" and doc.reference_name:
        bill_of_lading = frappe.get_doc("Bill Of Landing", doc.reference_name)

        # Validation: Accepted Qty + Rejected Qty <= Sample Size
        if int(doc.custom_accepted_qty or 0) + int(doc.custom_rejected_qty or 0) > int(doc.sample_size or 0):
            frappe.throw(f"The sum of Accepted Qty and Rejected Qty cannot exceed the Sample Size ({doc.sample_size}).")
        
        if int(doc.custom_accepted_qty or 0) + int(doc.custom_rejected_qty or 0) < int(doc.sample_size or 0):
            frappe.throw(f"The sum of Accepted Qty and Rejected Qty must be equal to the Sample Size  ({doc.sample_size}).")

        updated = False  # To track if any item was updated

        # Check if item_details_ph table exists and update accepted/rejected qty
        if hasattr(bill_of_lading, "item_details_ph") and bill_of_lading.item_details_ph:
            for item in bill_of_lading.item_details_ph:
                if item.item_code == doc.item_code:
                    item.accepted_qty = doc.custom_accepted_qty
                    item.rejected_qty = doc.custom_rejected_qty
                    item.quality_inspection_done = 1
                    updated = True

        # Check if item_details_th table exists and update accepted/rejected qty
        if hasattr(bill_of_lading, "item_details_th") and bill_of_lading.item_details_th:
            total_tyres_with_rim = 0
            total_tyres_without_rim = 0

            for item in bill_of_lading.item_details_th:
                if item.item_code == doc.item_code and item.tyre_type == doc.custom_type:
                    item.accepted_qty = doc.custom_accepted_qty
                    item.rejected_qty = doc.custom_rejected_qty
                    item.done_quality_inspection = 1
                    item.quality_inspection = doc.name  # Link Quality Inspection name
                    item.serial_no = doc.custom_accepted_serial_nos


                    # Calculate totals based on tyre_type

                    # if item.tyre_type == "With Rim":
                    #     total_tyres_with_rim += int(doc.custom_accepted_qty or 0)
                    # elif item.tyre_type == "Without Rim":
                    #     total_tyres_without_rim += int(doc.custom_accepted_qty or 0)

                    updated = True

            # # Update total fields in Bill Of Landing
            # bill_of_lading.total_tyres_with_rim = total_tyres_with_rim
            # bill_of_lading.total_tyres_without_rim = total_tyres_without_rim

            rejected_serials = doc.custom_rejected_serial_nos.split("\n")  # Extract serial numbers
    
            for serial_no in rejected_serials:
                serial_no = serial_no.strip()  # Remove any leading/trailing whitespace
                
                if serial_no:  # Ensure serial_no is not empty
                    serial_doc = frappe.get_doc("Serial No", serial_no)
                    serial_doc.status = "Inactive"  # Update status
                    serial_doc.save(ignore_permissions=True) 


        if not updated:
            frappe.throw(f"No matching item found with item code: {doc.item_code}")

        # Save Bill Of Landing with necessary flags
        bill_of_lading.flags.ignore_validate_update_after_submit = True
        bill_of_lading.flags.ignore_mandatory = True
        bill_of_lading.save(ignore_permissions=True)
