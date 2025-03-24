import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
    if not filters.get("customer"):
        frappe.throw(_("Please select a Customer"))

    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "customer_name",
            "label": _("Customer Name"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "fieldname": "customer_group",
            "label": _("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group",
            "width": 120
        },
        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "item_name",
            "label": _("Item Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "in_qty",
            "label": _("In Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "out_qty",
            "label": _("Out Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "available_qty",
            "label": _("Available Qty"),
            "fieldtype": "Float",
            "width": 120
        },
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "bol_id",
            "label": _("BOL ID"),
            "fieldtype": "Link",
            "options": "Bill of Landing",
            "width": 130
        },
        {
            "fieldname": "pick_list_id",
            "label": _("Pick List ID"),
            "fieldtype": "Link",
            "options": "Pick List",
            "width": 130
        }
    ]

def get_data(filters):
    # Get BOL data
    bol_data = frappe.db.sql("""
        SELECT 
            bl.customer as customer_name,
            c.customer_group as customer_group,
            itd.item_code,
            itd.item_name,
            COALESCE(itd.accepted_qty, 0) as in_qty,
            0 as out_qty,
            COALESCE(itd.accepted_qty, 0) as available_qty,
            COALESCE(bl.submission_date, bl.creation) as date,
            bl.name as bol_id,
            NULL as pick_list_id
        FROM
            `tabBill Of Landing` bl
            JOIN `tabCustomer` c ON bl.customer = c.name
            JOIN `tabBill Of Landing Item` itd ON bl.name = itd.parent
        WHERE
            bl.customer = %(customer)s
            AND bl.docstatus = 1
            AND bl.legal_doc_for_redelivery = 0
    """, filters, as_dict=1)

    # Get Pick List data
    pick_list_data = frappe.db.sql("""
        SELECT 
            pl.custom_pl_customer as customer_name,
            c.customer_group as customer_group,
            pl.custom_item_code as item_code,
            pl.custom_item_name as item_name,
            0 as in_qty,
            COALESCE(pl.custom_item_qty, 0) as out_qty,
            0 as available_qty,
            COALESCE(pl.creation, CURDATE()) as date,
            NULL as bol_id,
            pl.name as pick_list_id
        FROM
            `tabPick List` pl
            JOIN `tabCustomer` c ON pl.custom_pl_customer = c.name
        WHERE
            pl.custom_pl_customer = %(customer)s
            AND pl.docstatus = 1
            AND pl.custom_pl_status = 'Completed'
    """, filters, as_dict=1)

    # Combine data
    combined_data = bol_data + pick_list_data
    
    if not combined_data:
        return []

    # Sort by date with None handling
    def get_sort_date(row):
        if not row.date:
            return datetime.min
        return row.date if isinstance(row.date, datetime) else datetime.combine(row.date, datetime.min.time())

    combined_data.sort(key=get_sort_date)
    
    # Calculate running available quantity
    running_qty = {}
    for row in combined_data:
        item_code = row.item_code
        if item_code not in running_qty:
            running_qty[item_code] = 0
        
        # Ensure quantities are float
        in_qty = float(row.in_qty or 0)
        out_qty = float(row.out_qty or 0)
        
        running_qty[item_code] += in_qty - out_qty
        row.available_qty = running_qty[item_code]

    # Add total row
    if combined_data:
        total_in_qty = sum(float(d.in_qty or 0) for d in combined_data)
        total_out_qty = sum(float(d.out_qty or 0) for d in combined_data)
        
        total_row = frappe._dict({
            'customer_name': 'Total',
            'item_code': '',
            'item_name': '',
            'in_qty': total_in_qty,
            'out_qty': total_out_qty,
            'available_qty': sum(running_qty.values()),
            'bold': 1
        })
        combined_data.append(total_row)

    return combined_data
