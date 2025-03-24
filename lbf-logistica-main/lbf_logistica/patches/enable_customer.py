import frappe

def execute():
    try:
        doctype = frappe.get_doc("DocType", "Customer")
        doctype.is_tree = 0
        doctype.save()
        frappe.db.commit()
        print("Successfully enabled tree view for Customer")
    except Exception as e:
        print(f"Error enabling tree view: {str(e)}")