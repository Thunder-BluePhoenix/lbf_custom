__version__ = "0.0.1"
import frappe
from frappe.utils import flt
import erpnext.stock.utils

@frappe.whitelist()
def get_custom_incoming_rate(args, method=None):
    # pass
    """
    Custom method to handle incoming rate calculation with multiple fallback strategies

    :param args: Dictionary containing item details
    :param raise_error_if_no_rate: Whether to raise an error if no rate is found
    :return: Calculated incoming rate (float)
    """
    try:
        item_code = args.get('item_code')
        warehouse = args.get('warehouse')

        if not item_code:
            if raise_error_if_no_rate:
                frappe.throw(f"Item code is required to fetch the rate.")
            return 0

        # Strategy 1: Get valuation rate from item
        item = frappe.get_cached_doc('Item', item_code)
        if item.valuation_rate:
            # return flt(item.valuation_rate)
            return 0

        # Strategy 2: Get average rate from stock ledger
        stock_value_query = frappe.db.sql("""
            SELECT 
                SUM(stock_value) / SUM(actual_qty) as avg_rate
            FROM `tabStock Ledger Entry`
            WHERE 
                item_code = %s 
                AND warehouse = %s 
                AND actual_qty > 0
        """, (item_code, warehouse), as_dict=True)

        if stock_value_query and stock_value_query[0].get('avg_rate'):
            return flt(stock_value_query[0]['avg_rate'])
        
          # Strategy 4: Get standard cost from item
        if item.standard_cost:
            # return item.standard_cost
            return 0
        
         # Final fallback: return 1 to prevent division by zero
        return 1

        # Strategy 3: Return a default rate of 0
        if raise_error_if_no_rate:
            frappe.throw(_("No rate found for item {0} in warehouse {1}").format(item_code, warehouse))
        return 0

    except Exception as e:
        frappe.log_error(f"Rate Calculation Error: {str(e)}", "Incoming Rate Error")
        return 0  # Return 0 to prevent further errors
 

erpnext.stock.utils.get_incoming_rate = get_custom_incoming_rate