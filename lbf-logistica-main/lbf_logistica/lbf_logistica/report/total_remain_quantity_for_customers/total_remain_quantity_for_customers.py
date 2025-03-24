import frappe
from frappe import _
from datetime import datetime



def execute(filters=None):
    # Query to get total accepted quantity from BOL for each customer
    bol_data = frappe.db.sql("""
        SELECT
            bl.customer as customer_name,
            SUM(COALESCE(itd.accepted_qty, 0)) as total_in_qty
        FROM
            `tabBill Of Landing` bl
            JOIN `tabBill Of Landing Item` itd ON bl.name = itd.parent
        WHERE
            bl.docstatus = 1
            AND bl.legal_doc_for_redelivery = 0
        GROUP BY bl.customer
    """, as_dict=1)
    
    # Query to get total item quantity from Pick List for each customer
    pick_list_data = frappe.db.sql("""
        SELECT
            pl.custom_pl_customer as customer_name,
            SUM(COALESCE(pl.custom_item_qty, 0)) as total_out_qty
        FROM
            `tabPick List` pl
        WHERE
            pl.docstatus = 1
            AND pl.custom_pl_status = 'Completed'
        GROUP BY pl.custom_pl_customer
    """, as_dict=1)
    
    # Merge the results to calculate Total Qty
    customer_data = {}
    
    # Add BOL data to the dictionary
    for row in bol_data:
        customer_data[row['customer_name']] = {
            'customer_name': row['customer_name'],
            'total_in_qty': row['total_in_qty'],
            'total_out_qty': 0  # default if no Pick List data
        }
    
    # Add Pick List data to the dictionary
    for row in pick_list_data:
        if row['customer_name'] in customer_data:
            customer_data[row['customer_name']]['total_out_qty'] = row['total_out_qty']
        else:
            customer_data[row['customer_name']] = {
                'customer_name': row['customer_name'],
                'total_in_qty': 0,  # default if no BOL data
                'total_out_qty': row['total_out_qty']
            }
    
    # Prepare the result with calculated Total Qty
    result = []
    for customer, data in customer_data.items():
        total_qty = data['total_in_qty'] - data['total_out_qty']
        result.append({
            'customer_name': data['customer_name'],
            'total_qty': total_qty
        })
    
    # Define the columns for the report
    columns = [
        {
            'fieldname': 'customer_name',
            'label': 'Customer Name',
            'fieldtype': 'Data',
            'width': 200
        },
        {
            'fieldname': 'total_qty',
            'label': 'Total Qty',
            'fieldtype': 'Float',
            'width': 150
        }
    ]
    
    return columns, result


