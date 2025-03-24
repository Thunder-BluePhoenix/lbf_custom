import frappe
from frappe import _

@frappe.whitelist()
def scan_serial_no_barcode(barcode, stock_entry_doc):
    """
    Scan barcode and populate Stock Entry items based on Serial No
    
    :param barcode: Scanned barcode
    :param stock_entry_doc: Stock Entry document
    :return: Populated Stock Entry item details
    """
    try:
        # Find Serial No with matching barcode
        serial_no = frappe.get_all('Serial No', 
            filters={'custom_barcode': barcode},
            fields=['name', 'item_code', 'warehouse', 'batch_no']
        )
        
        if not serial_no:
            frappe.msgprint(_("No Serial found with this barcode"))
            return None
        
        # Get the first matching Serial No
        serial_data = serial_no[0]
        
        # Prepare item details for Stock Entry
        item_details = {
            'item_code': serial_data['item_code'],
            'serial_no': serial_data['name'],
            'from_warehouse': serial_data['warehouse'],
            'qty': 1,  # Explicitly set quantity
            'uom': 'Nos',  # Set default UOM
            'allow_zero_valuation_rate': 1 ,
            "actual_qty": 1,
            'batch': serial_data['batch_no']
            # Add other relevant fields as needed
        }
        
        return item_details
    
    except frappe.exceptions.ValidationError:
        # Validation error if item is not found
        frappe.log_error("Validation Error in Barcode Scanning")
        frappe.msgprint(_("No valid item or serial number found for the scanned barcode."))
        return None

    except Exception as e:
        # Log any other exceptions
        frappe.log_error(f"Barcode Scanning Error: {str(e)}", "Barcode Scanning")
        frappe.msgprint(_("Error scanning barcode: {0}").format(str(e)))
        return None


@frappe.whitelist()
def populate_stock_entry_from_bundle(bundle_id, stock_entry_doc):
    """
    Populate Stock Entry items based on Serial and Batch Bundle
    
    :param bundle_id: Custom Serial and Batch Bundle ID
    :param stock_entry_doc: Stock Entry document
    :return: List of populated Stock Entry item details
    """
    try:
        # Fetch the Serial and Batch Bundle document
        bundle_doc = frappe.get_doc('Serial and Batch Bundle', bundle_id)
        
        if not bundle_doc or not bundle_doc.entries:
            frappe.msgprint(_("No entries found in the selected bundle"))
            return None
        
        # Prepare a list to store item details
        bundle_item_details = []
        
        # Process each entry in the bundle
        for entry in bundle_doc.entries:
            # Fetch full Serial No details
            try:
                serial_no_doc = frappe.get_doc('Serial No', entry.serial_no)
                
                # Prepare item details for Stock Entry
                item_details = {
                    'item_code': serial_no_doc.item_code,
                    'serial_no': serial_no_doc.name,
                    'from_warehouse': serial_no_doc.warehouse,
                    'qty': 1,
                    'uom': 'Nos',
                    'allow_zero_valuation_rate': 1,
                    'actual_qty': 1,
                    'batch': serial_no_doc.batch_no if hasattr(serial_no_doc, 'batch_no') else None,
                    # Add any additional fields you want to populate
                    'custom_serial_and_batch_bundle_id': bundle_id,
                    'barcode':serial_no_doc.custom_barcode
                }
                
                bundle_item_details.append(item_details)
            
            except frappe.DoesNotExistError:
                # Log if a specific serial no is not found
                frappe.log_error(f"Serial No {entry.serial_no} not found", "Bundle Population Error")
                continue
        
        return bundle_item_details
    
    except Exception as e:
        frappe.log_error(f"Error populating from Serial and Batch Bundle: {str(e)}", "Bundle Population Error")
        frappe.msgprint(_("Error populating items from bundle: {0}").format(str(e)))
        return None


