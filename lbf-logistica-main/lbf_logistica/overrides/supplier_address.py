import frappe
from frappe import _

@frappe.whitelist()
def update_address_and_contact(doc, method):
    # Determine the value to set for custom_transporter_address and custom_transporter_contact
    transporter_value = 1 if doc.is_transporter else 0

    # Update linked addresses
    addresses = frappe.db.sql("""
        SELECT DISTINCT parent 
        FROM `tabDynamic Link` 
        WHERE parenttype = 'Address'
        AND link_doctype = 'Supplier'
        AND link_name = %s
    """, (doc.name,), as_dict=True)

    for address in addresses:
        frappe.db.set_value("Address", address["parent"], "custom_transporter_address", transporter_value)

    # Update linked contacts
    contacts = frappe.db.sql("""
        SELECT DISTINCT parent 
        FROM `tabDynamic Link` 
        WHERE parenttype = 'Contact'
        AND link_doctype = 'Supplier'
        AND link_name = %s
    """, (doc.name,), as_dict=True)

    for contact in contacts:
        frappe.db.set_value("Contact", contact["parent"], "custom_transporter_contact", transporter_value)

    # Commit changes to the database
    frappe.db.commit()




@frappe.whitelist()
def update_supplier_in_customer(doc, method):
    # if doc.is_transporter or doc.custom_cutoff_start_time or doc.custom_cutoff_end_time:
        # Fetch all customers that have the supplier in their custom_supplier table
        customers = frappe.get_all('Customer', fields=['name'])

        # Loop through each customer and update the custom_supplier table
        for customer in customers:
            customer_doc = frappe.get_doc('Customer', customer['name'])

            for row in customer_doc.custom_suppliers:
                if row.supplier == doc.name:
                    row.is_transporter = doc.is_transporter
                    row.cutoff_start_time = doc.custom_cutoff_start_time
                    row.cutoff_end_time = doc.custom_cutoff_end_time

            # Save the updated customer document
            customer_doc.save()
            frappe.db.commit()



