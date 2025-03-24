import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta, date
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
    def validate(self):
        # Skip certain validations by not calling the super method
        pass

@frappe.whitelist(allow_guest=True)
def check_and_validate_pricingrule(doc, method=None):
    if doc.custom_peneus_hub:
        # Fetch related Pricing Rule
        pricing_rule = get_pricing_rule(doc)
        
        if pricing_rule:
            # Apply handling charges
            apply_handling_charges(doc, pricing_rule)
            populate_invoice_table(doc)

    if doc.custom_tyre_hotel:
        tyre_hotel_charge = get_tyre_hotel_setting(doc)

        if tyre_hotel_charge:
            apply_tyre_hotel_charges(doc)
            populate_th_invoice_table(doc)

    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate = True
    doc.flags.ignore_mandatory = True


@frappe.whitelist(allow_guest=True)
def get_tyre_hotel_setting(doc, method=None):
    tyre_hotel_settings = frappe.get_doc("Tyre Hotel Pricing Rule", doc.customer)
    if tyre_hotel_settings.amount_with_rim is None or tyre_hotel_settings.amount_without_rim is None:
         return
    return tyre_hotel_settings

@frappe.whitelist(allow_guest=True)
def apply_tyre_hotel_charges(doc, method=None):
    tyre_hotel_settings = frappe.get_doc("Tyre Hotel Pricing Rule", doc.customer)
    if tyre_hotel_settings.amount_with_rim is None or tyre_hotel_settings.amount_without_rim is None:
         return
    amount_with_rim = tyre_hotel_settings.amount_with_rim
    amount_without_rim = tyre_hotel_settings.amount_without_rim

    if tyre_hotel_settings.minimum_threshold_days:
        doc.custom_minimum_threshold_days = tyre_hotel_settings.minimum_threshold_days

    doc.custom_charges_with_rim = amount_with_rim
    doc.custom_charges_without_rim = amount_without_rim
    



@frappe.whitelist(allow_guest=True)
def get_pricing_rule(doc, method=None):
    """
    Fetch Pricing Rule based on customer and Peneus Hub checkbox
    """
    customer = doc.customer
    pricing_rules = frappe.get_all(
        'Pricing Rule',
        filters={
            'custom_customerr': customer,
        }
    )
    
    return frappe.get_doc('Pricing Rule', pricing_rules[0]) if pricing_rules else None

@frappe.whitelist(allow_guest=True)
def apply_handling_charges(doc, pricing_rule):
    if pricing_rule.custom_handling_in:
        doc.custom_handling_in_charges = pricing_rule.custom_amount_handling_in
    
    if pricing_rule.custom_handling_out:
        doc.custom_handling_out_charges = pricing_rule.custom_amount_handling_out
    
    doc.custom_storage_rate_per_day = pricing_rule.custom_amount_cost_over_time_charges
    doc.custom_lbf_currency = pricing_rule.custom_currencycost_over_time_charges

@frappe.whitelist(allow_guest=True)
def populate_invoice_table(doc):
    previous_invoices = frappe.get_all(
        'Sales Invoice',
        filters={
            'customer': doc.customer,
            'custom_peneus_hub': 1,
            'docstatus': 1,
            # 'custom_posting_datetime' : ('!=', ''),
            # 'custom_submission_date': ('!=', ''),
            'custom_start_date_for_storage_cost_' : ('!=', ''),
            'custom_end_date_for_storage_cost': ('!=', '')
        },
        order_by='creation desc'
    )

    # Fetch relevant Bill of Landing and Pick List documents
    bill_of_landings = frappe.get_all(
        'Bill Of Landing',
        filters={
            'customer': doc.customer,
            'service': 'Peneus hub',
            'docstatus': 1,
            'legal_doc_for_redelivery': 0,
            'submission_datetime' : ('!=', ''),
            # 'submission_date': ('!=', '')
        },
        order_by='submission_datetime'
    )
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22bill_of_landings",bill_of_landings)

    pick_lists = frappe.get_all(
        'Pick List',
        filters={
            'custom_pl_customer': doc.customer,
            'custom_service': 'Peneus hub',
            'docstatus': 1,
            'custom_pl_status': 'Completed',
            'custom_submission_datetime' : ('!=', ''),
            # 'custom_submission_date': ('!=', '')
        },
        order_by='custom_submission_datetime'
    )
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22",pick_lists)

    doc.custom_storage_fees_for_items = []
    if not previous_invoices:
        # First invoice - use the current invoice's start and end dates
        doc_start_date = frappe.utils.getdate(doc.custom_start_date_for_storage_cost_)
        doc_end_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
        

        # Filter Bill of Landings and Pick Lists within the date range
        wrt_inv_bill_of_landings = [
            bl for bl in bill_of_landings
            if doc_start_date <= frappe.get_doc('Bill Of Landing', bl['name']).submission_datetime.date() <= doc_end_date
        ]
        
        wrt_inv_pick_lists = [
            pl for pl in pick_lists
            if doc_start_date <= frappe.get_doc('Pick List', pl['name']).custom_submission_datetime.date() <= doc_end_date
        ]

        populate_invoice_rows(doc, wrt_inv_bill_of_landings, wrt_inv_pick_lists)
    else:
        # Subsequent invoices
        last_invoice = frappe.get_doc('Sales Invoice', previous_invoices[0]['name'])
        doc_start_date = frappe.utils.getdate(doc.custom_start_date_for_storage_cost_)
        doc_end_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
        last_invoice_end_date = frappe.utils.getdate(last_invoice.custom_end_date_for_storage_cost)

        # Filter Bill of Landings and Pick Lists from last invoice's end date to current invoice's end date
        filtered_bill_of_landings = [
            bl for bl in bill_of_landings
            if last_invoice_end_date < frappe.get_doc('Bill Of Landing', bl['name']).submission_datetime.date() <= doc_end_date
        ]
        
        filtered_pick_lists = [
            pl for pl in pick_lists
            if last_invoice_end_date < frappe.get_doc('Pick List', pl['name']).custom_submission_datetime.date() <= doc_end_date
        ]
        
        # Get the last row from the previous invoice
        last_row = last_invoice.custom_storage_fees_for_items[-1]
        
        populate_subsequent_invoice_rows(
            doc,
            last_row,
            filtered_bill_of_landings,
            filtered_pick_lists
        )

@frappe.whitelist(allow_guest=True)
def populate_invoice_rows(doc, bill_of_landings, pick_lists):
    used_bill_of_landings = set()
    used_pick_lists = set()

    pick_list_map = {}
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        pl_date = pl_doc.custom_submission_datetime.date()
        if pl_date not in pick_list_map:
            pick_list_map[pl_date] = []
        pick_list_map[pl_date].append(pl_doc)

    bill_of_landing_map = {}
    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        bl_date = bl_doc.submission_datetime.date()
        if bl_date not in bill_of_landing_map:
            bill_of_landing_map[bl_date] = []
        bill_of_landing_map[bl_date].append(bl_doc)

    combined_docs = []

    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        if bl_doc.name not in used_bill_of_landings:
            combined_docs.append({
                'type': 'Bill Of Landing',
                'doc': bl_doc,
                'creation': bl_doc.submission_datetime,
                'received_qty': bl_doc.total_qty_accepted,
                'received_items': bl_doc.all_item_serial_no,
                'out_items': None,
                'sold_qty': 0
            })
            used_bill_of_landings.add(bl_doc.name)

    # Add Pick Lists, ensuring no duplicates
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        if pl_doc.name not in used_pick_lists:
            combined_docs.append({
                'type': 'Pick List',
                'doc': pl_doc,
                'creation': pl_doc.custom_submission_datetime,
                'sold_qty': pl_doc.custom_item_qty,
                'received_items': None,
                'out_items': pl_doc.custom_all_item_serial_no_out,
                'received_qty': 0
            })
            used_pick_lists.add(pl_doc.name)

    # Sort combined documents by creation datetime
    combined_docs.sort(key=lambda x: x['creation'])

    running_final_qty = 0
    previous_row_date = None
    prev_sto_itm = []

    for i, doc_entry in enumerate(combined_docs):
        new_row = doc.append('custom_storage_fees_for_items', {})
        new_row.date = doc_entry['creation'].date()

        if doc_entry['type'] == 'Bill Of Landing':
            new_row.bill_of_landing = doc_entry['doc'].name
            new_row.received_qty = doc_entry['received_qty']
            new_row.received_items = doc_entry['received_items']
            new_row.out_items = doc_entry['out_items']

            matching_pick_lists = pick_list_map.get(new_row.date, [])
            used_matching_pick_lists = [
                pl for pl in matching_pick_lists
                if pl.name not in used_pick_lists
            ]
            if used_matching_pick_lists:
                pl_doc = used_matching_pick_lists[0]
                new_row.pick_list = pl_doc.name
                new_row.sold_qty = pl_doc.custom_item_qty
                used_pick_lists.add(pl_doc.name)
            else:
                new_row.sold_qty = 0

        else:
            new_row.pick_list = doc_entry['doc'].name
            new_row.sold_qty = doc_entry['sold_qty']
            new_row.received_items = doc_entry['received_items']
            new_row.out_items = doc_entry['out_items']
        
            matching_bill_of_landings = bill_of_landing_map.get(new_row.date, [])
            used_matching_bill_of_landings = [
                bl for bl in matching_bill_of_landings
                if bl.name not in used_bill_of_landings
            ]
            if used_matching_bill_of_landings:
                bl_doc = used_matching_bill_of_landings[0]
                new_row.bill_of_landing = bl_doc.name
                new_row.received_qty = bl_doc.total_qty_accepted
                used_bill_of_landings.add(bl_doc.name)
            else:
                new_row.received_qty = 0

        running_final_qty += float(new_row.received_qty) - float(new_row.sold_qty)
        new_row.final_qty = float(running_final_qty)

        new_row_date = frappe.utils.getdate(new_row.date)
        end_date_inv = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)


        cur_recv_items = []
        if new_row.received_items:
            cur_recv_items = new_row.received_items.split('\n') if new_row.received_items else []
        
        cur_out_items = []
        if new_row.out_items:
            cur_out_items = new_row.out_items.split('\n') if new_row.out_items else []

        final_sto_itm = prev_sto_itm.copy()
        final_sto_itm.extend(cur_recv_items)

        final_sto_itm = [item for item in final_sto_itm if item not in cur_out_items]
        final_sto_itm = sorted(final_sto_itm, key=lambda x: int(x.replace('SN', '')))
        new_row.final_stored_items = '\n'.join(final_sto_itm) if final_sto_itm else ''

        prev_sto_itm = final_sto_itm

        # Similar logic to previous implementation, but with modifications to use start and end dates
        if i == 0:
            if len(combined_docs) == 1:
                new_row.number_of_days = (end_date_inv - new_row_date).days + 1
            else:
                next_row_date = combined_docs[i + 1]['creation'].date()
                new_row.number_of_days = (next_row_date - new_row_date).days
        else:
            if i < len(combined_docs) - 1:
                next_row_date = combined_docs[i + 1]['creation'].date()
                new_row.number_of_days = (next_row_date - new_row_date).days
            else:
                new_row.number_of_days = (end_date_inv - new_row_date).days + 1

        new_row.daily_rate = doc.custom_storage_rate_per_day
        new_row.daily_sub_total = new_row.final_qty * new_row.daily_rate
        new_row.cost_for_the_days = new_row.number_of_days * new_row.daily_sub_total
        new_row.handling_in_charges = float(new_row.received_qty) * float(doc.custom_handling_in_charges)
        new_row.handling_out_charges = float(new_row.sold_qty) * float(doc.custom_handling_out_charges)
        new_row.amount = new_row.cost_for_the_days + new_row.handling_in_charges + new_row.handling_out_charges
        previous_row_date = new_row.date
    
    total_amount = sum(row.amount for row in doc.custom_storage_fees_for_items)
    doc.custom_total_cost = total_amount
    doc.custom_grand_total_cost = total_amount
    doc.custom_total_in_words = frappe.utils.money_in_words(total_amount)

@frappe.whitelist(allow_guest=True)
def populate_subsequent_invoice_rows(doc, last_row, bill_of_landings, pick_lists):
    """
    Populate storage fees for subsequent invoices after the first one
    
    Args:
        doc (Sales Invoice): Current sales invoice document
        last_row (dict): Last row from the previous invoice
        bill_of_landings (list): List of Bill of Landing documents
        pick_lists (list): List of Pick List documents
    """
    pick_list_map = {}
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        pl_date = pl_doc.custom_submission_datetime.date()
        if pl_date not in pick_list_map:
            pick_list_map[pl_date] = []
        pick_list_map[pl_date].append(pl_doc)

    bill_of_landing_map = {}
    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        bl_date = bl_doc.submission_datetime.date()
        if bl_date not in bill_of_landing_map:
            bill_of_landing_map[bl_date] = []
        bill_of_landing_map[bl_date].append(bl_doc)

    used_bill_of_landings = set()
    used_pick_lists = set()
    combined_docs = []

    # Add Bill of Landings to combined documents
    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        if bl_doc.name not in used_bill_of_landings:
            combined_docs.append({
                'type': 'Bill Of Landing',
                'doc': bl_doc,
                'creation': bl_doc.submission_datetime,
                'received_qty': bl_doc.total_qty_accepted,
                'received_items': bl_doc.all_item_serial_no,
                'out_items': None,
                'sold_qty': 0
            })
            used_bill_of_landings.add(bl_doc.name)

    # Add Pick Lists to combined documents
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        if pl_doc.name not in used_pick_lists:
            combined_docs.append({
                'type': 'Pick List',
                'doc': pl_doc,
                'creation': pl_doc.custom_submission_datetime,
                'sold_qty': pl_doc.custom_item_qty,
                'received_items': None,
                'out_items': pl_doc.custom_all_item_serial_no_out,
                'received_qty': 0
            })
            used_pick_lists.add(pl_doc.name)

    # Sort combined documents by submission datetime
    combined_docs.sort(key=lambda x: x['creation'])

    # Initialize running final quantity from the last invoice's final quantity
    running_final_qty = float(last_row.final_qty)
    prev_sto_itm = last_row.final_stored_items.split('\n') if last_row.final_stored_items else []

    # Add the first row with the start date of the current invoice
    first_row = doc.append('custom_storage_fees_for_items', {})
    first_row.date = frappe.utils.getdate(doc.custom_start_date_for_storage_cost_)
    first_row.final_qty = running_final_qty
    first_row.received_qty = 0
    first_row.sold_qty = 0
    first_row.final_stored_items = prev_sto_itm
    first_row.received_items = ""
    first_row.out_items = ""

    # Calculate number of days for the first row
    if combined_docs:
        next_row_date = combined_docs[0]['creation'].date()
    else:
        next_row_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
    
    first_row.number_of_days = (next_row_date - first_row.date).days

    # Calculate costs for the first row
    first_row.daily_rate = doc.custom_storage_rate_per_day
    first_row.daily_sub_total = first_row.final_qty * first_row.daily_rate
    first_row.cost_for_the_days = first_row.number_of_days * first_row.daily_sub_total
    first_row.handling_in_charges = 0  # No handling charges for the first row
    first_row.handling_out_charges = 0
    first_row.amount = first_row.cost_for_the_days

    # Process the rest of the documents
    for i, doc_entry in enumerate(combined_docs):
        new_row = doc.append('custom_storage_fees_for_items', {})
        
        # Use submission_date instead of creation date
        new_row.date = doc_entry['creation'].date()

        if doc_entry['type'] == 'Bill Of Landing':
            new_row.bill_of_landing = doc_entry['doc'].name
            new_row.received_qty = doc_entry['received_qty']
            new_row.received_items = doc_entry['doc'].all_item_serial_no
            new_row.out_items = ""

            # Match Pick Lists for the same date
            matching_pick_lists = pick_list_map.get(new_row.date, [])
            used_matching_pick_lists = [
                pl for pl in matching_pick_lists
                if pl.name not in used_pick_lists
            ]
            if used_matching_pick_lists:
                pl_doc = used_matching_pick_lists[0]
                new_row.pick_list = pl_doc.name
                new_row.sold_qty = pl_doc.custom_item_qty
                used_pick_lists.add(pl_doc.name)
            else:
                new_row.sold_qty = 0

        else:  # Pick List
            new_row.pick_list = doc_entry['doc'].name
            new_row.sold_qty = doc_entry['sold_qty']
            new_row.received_items = ""
            new_row.out_items = doc_entry['doc'].custom_all_item_serial_no_out
            
            # Match Bill of Landings for the same date
            matching_bill_of_landings = bill_of_landing_map.get(new_row.date, [])
            used_matching_bill_of_landings = [
                bl for bl in matching_bill_of_landings
                if bl.name not in used_bill_of_landings
            ]
            if used_matching_bill_of_landings:
                bl_doc = used_matching_bill_of_landings[0]
                new_row.bill_of_landing = bl_doc.name
                new_row.received_qty = bl_doc.total_qty_accepted
                used_bill_of_landings.add(bl_doc.name)
            else:
                new_row.received_qty = 0

        # Calculate running final quantity
        running_final_qty += float(new_row.received_qty) - float(new_row.sold_qty)
        new_row.final_qty = float(running_final_qty)

        # Calculate number of days
        if i < len(combined_docs) - 1:
            next_row_date = combined_docs[i + 1]['creation'].date()
        else:
            next_row_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
        
        new_row.number_of_days = (next_row_date - new_row.date).days +1

        cur_recv_items = []
        if new_row.received_items:
            cur_recv_items = new_row.received_items.split('\n') if new_row.received_items else []
        
        cur_out_items = []
        if new_row.out_items:
            cur_out_items = new_row.out_items.split('\n') if new_row.out_items else []

        final_sto_itm = prev_sto_itm.copy()
        final_sto_itm.extend(cur_recv_items)

        final_sto_itm = [item for item in final_sto_itm if item not in cur_out_items]
        final_sto_itm = sorted(final_sto_itm, key=lambda x: int(x.replace('SN', '')))
        new_row.final_stored_items = '\n'.join(final_sto_itm) if final_sto_itm else ''

        prev_sto_itm = final_sto_itm

        # Cost calculations
        new_row.daily_rate = doc.custom_storage_rate_per_day
        new_row.daily_sub_total = new_row.final_qty * new_row.daily_rate
        new_row.cost_for_the_days = new_row.number_of_days * new_row.daily_sub_total
        new_row.handling_in_charges = float(new_row.received_qty) * float(doc.custom_handling_in_charges)
        new_row.handling_out_charges = float(new_row.sold_qty) * float(doc.custom_handling_out_charges)
        new_row.amount = new_row.cost_for_the_days + new_row.handling_in_charges + new_row.handling_out_charges

    # Calculate total amount for the invoice
    total_amount = sum(row.amount for row in doc.custom_storage_fees_for_items)
    doc.custom_total_cost = total_amount
    doc.custom_grand_total_cost = total_amount
    doc.custom_total_in_words = frappe.utils.money_in_words(total_amount)











@frappe.whitelist(allow_guest=True)
def populate_th_invoice_table(doc):
    previous_invoices = frappe.get_all(
        'Sales Invoice',
        filters={
            'customer': doc.customer,
            'custom_tyre_hotel': 1,
            'docstatus': 1,
            # 'custom_posting_datetime' : ('!=', ''),
            # 'custom_submission_date': ('!=', ''),
            'custom_start_date_for_storage_cost_' : ('!=', ''),
            'custom_end_date_for_storage_cost': ('!=', '')
        },
        order_by='creation desc'
    )

    # Fetch relevant Bill of Landing and Pick List documents
    bill_of_landings = frappe.get_all(
        'Bill Of Landing',
        filters={
            'customer': doc.customer,
            'service': 'Tyre Hotel',
            'docstatus': 1,
            'legal_doc_for_redelivery': 0,
            'submission_datetime' : ('!=', ''),
            # 'submission_date': ('!=', '')
        },
        order_by='submission_datetime'
    )
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22bill_of_landings",bill_of_landings)

    pick_lists = frappe.get_all(
        'Pick List',
        filters={
            'custom_pl_customer': doc.customer,
            'custom_service': 'Tyre Hotel',
            'docstatus': 1,
            'custom_pl_status': 'Completed',
            'custom_submission_datetime' : ('!=', ''),
            # 'custom_submission_date': ('!=', '')
        },
        order_by='custom_submission_datetime'
    )
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22",pick_lists)

    doc.custom_storage_fees_for_itemsth = []
    if not previous_invoices:
        # First invoice - use the current invoice's start and end dates
        doc_start_date = frappe.utils.getdate(doc.custom_start_date_for_storage_cost_)
        doc_end_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
        

        # Filter Bill of Landings and Pick Lists within the date range
        wrt_inv_bill_of_landings = [
            bl for bl in bill_of_landings
            if doc_start_date <= frappe.get_doc('Bill Of Landing', bl['name']).submission_datetime.date() <= doc_end_date
        ]
        
        wrt_inv_pick_lists = [
            pl for pl in pick_lists
            if doc_start_date <= frappe.get_doc('Pick List', pl['name']).custom_submission_datetime.date() <= doc_end_date
        ]

        populate_th_invoice_rows(doc, wrt_inv_bill_of_landings, wrt_inv_pick_lists)
    else:
        # Subsequent invoices
        last_invoice = frappe.get_doc('Sales Invoice', previous_invoices[0]['name'])
        doc_start_date = frappe.utils.getdate(doc.custom_start_date_for_storage_cost_)
        doc_end_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
        last_invoice_end_date = frappe.utils.getdate(last_invoice.custom_end_date_for_storage_cost)

        # Filter Bill of Landings and Pick Lists from last invoice's end date to current invoice's end date
        filtered_bill_of_landings = [
            bl for bl in bill_of_landings
            if last_invoice_end_date < frappe.get_doc('Bill Of Landing', bl['name']).submission_datetime.date() <= doc_end_date
        ]
        
        filtered_pick_lists = [
            pl for pl in pick_lists
            if last_invoice_end_date < frappe.get_doc('Pick List', pl['name']).custom_submission_datetime.date() <= doc_end_date
        ]
        
        # Get the last row from the previous invoice
        last_row = last_invoice.custom_storage_fees_for_items[-1]
        
        populate_subsequent_th_invoice_rows(
            doc,
            last_row,
            filtered_bill_of_landings,
            filtered_pick_lists
        )




@frappe.whitelist(allow_guest=True)
def populate_th_invoice_rows(doc, bill_of_landings, pick_lists):
    used_bill_of_landings = set()
    used_pick_lists = set()

    pick_list_map = {}
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        pl_date = pl_doc.custom_submission_datetime.date()
        if pl_date not in pick_list_map:
            pick_list_map[pl_date] = []
        pick_list_map[pl_date].append(pl_doc)

    bill_of_landing_map = {}
    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        bl_date = bl_doc.submission_datetime.date()
        if bl_date not in bill_of_landing_map:
            bill_of_landing_map[bl_date] = []
        bill_of_landing_map[bl_date].append(bl_doc)

    combined_docs = []

    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        if bl_doc.name not in used_bill_of_landings:
            # Default to 0 if values are None
            received_qty_withrim = float(bl_doc.total_tyres_with_rim or 0)
            received_qty_withoutrim = float(bl_doc.total_tyres_without_rim or 0)
            combined_docs.append({
                'type': 'Bill Of Landing',
                'doc': bl_doc,
                'creation': bl_doc.submission_datetime,
                'received_qty_withrim': received_qty_withrim,
                'received_qty_withoutrim': received_qty_withoutrim,
                'received_items': bl_doc.all_item_serial_no,
                'out_items': None,
                'sold_qty_withrim': 0,
                'sold_qty_withoutrim': 0
            })
            used_bill_of_landings.add(bl_doc.name)

    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        if pl_doc.name not in used_pick_lists:
            # Default to 0 if values are None.
            item_qty = float(pl_doc.custom_item_qty or 0)
            sold_qty_withrim = item_qty if pl_doc.custom_item_type == "With Rim" else 0
            sold_qty_withoutrim = item_qty if pl_doc.custom_item_type == "Without Rim" else 0
            combined_docs.append({
                'type': 'Pick List',
                'doc': pl_doc,
                'creation': pl_doc.custom_submission_datetime,
                'sold_qty_withrim': sold_qty_withrim,
                'sold_qty_withoutrim': sold_qty_withoutrim,
                'received_items': None,
                'out_items': pl_doc.custom_all_item_serial_no_out,
                'received_qty_withrim': 0,
                'received_qty_withoutrim': 0
            })
            used_pick_lists.add(pl_doc.name)

    combined_docs.sort(key=lambda x: x['creation'])

    running_final_qty_withrim = 0
    running_final_qty_withoutrim = 0
    previous_row_date = None
    prev_sto_itm = []

    for i, doc_entry in enumerate(combined_docs):
        new_row = doc.append('custom_storage_fees_for_itemsth', {})
        new_row.date = doc_entry['creation'].date()

        if doc_entry['type'] == 'Bill Of Landing':
            new_row.bill_of_landing = doc_entry['doc'].name
            new_row.received_qty_withrim = doc_entry['received_qty_withrim']
            new_row.received_qty_withoutrim = doc_entry['received_qty_withoutrim']
            new_row.received_items = doc_entry['received_items']
            new_row.out_items = doc_entry['out_items']

            matching_pick_lists = pick_list_map.get(new_row.date, [])
            used_matching_pick_lists = [
                pl for pl in matching_pick_lists
                if pl.name not in used_pick_lists
            ]
            if used_matching_pick_lists:
                pl_doc = used_matching_pick_lists[0]
                # Default to 0 if values are None
                item_qty = float(pl_doc.custom_item_qty or 0)
                new_row.pick_list = pl_doc.name
                new_row.sold_qty_withrim = item_qty if pl_doc.custom_item_type == "with rim" else 0
                new_row.sold_qty_withoutrim = item_qty if pl_doc.custom_item_type == "without rim" else 0
                used_pick_lists.add(pl_doc.name)
            else:
                new_row.sold_qty_withrim = 0
                new_row.sold_qty_withoutrim = 0

        else:
            new_row.pick_list = doc_entry['doc'].name
            new_row.sold_qty_withrim = doc_entry['sold_qty_withrim']
            new_row.sold_qty_withoutrim = doc_entry['sold_qty_withoutrim']
            new_row.received_items = doc_entry['received_items']
            new_row.out_items = doc_entry['out_items']

            matching_bill_of_landings = bill_of_landing_map.get(new_row.date, [])
            used_matching_bill_of_landings = [
                bl for bl in matching_bill_of_landings
                if bl.name not in used_bill_of_landings
            ]
            if used_matching_bill_of_landings:
                bl_doc = used_matching_bill_of_landings[0]
                # Default to 0 if values are None
                new_row.bill_of_landing = bl_doc.name
                new_row.received_qty_withrim = float(bl_doc.total_tyres_with_rim or 0)
                new_row.received_qty_withoutrim = float(bl_doc.total_tyres_without_rim or 0)
                used_bill_of_landings.add(bl_doc.name)
            else:
                new_row.received_qty_withrim = 0
                new_row.received_qty_withoutrim = 0

        # Ensure we're working with float values, defaulting to 0 for None
        received_withrim = float(new_row.received_qty_withrim or 0)
        received_withoutrim = float(new_row.received_qty_withoutrim or 0)
        sold_withrim = float(new_row.sold_qty_withrim or 0)
        sold_withoutrim = float(new_row.sold_qty_withoutrim or 0)

        running_final_qty_withrim += received_withrim - sold_withrim
        running_final_qty_withoutrim += received_withoutrim - sold_withoutrim
        
        new_row.final_qty_withrim = running_final_qty_withrim
        new_row.final_qty_withoutrim = running_final_qty_withoutrim

        new_row_date = frappe.utils.getdate(new_row.date)
        end_date_inv = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)

        if i == 0:
            if len(combined_docs) == 1:
                new_row.number_of_days = (end_date_inv - new_row_date).days + 1
            else:
                next_row_date = combined_docs[i + 1]['creation'].date()
                new_row.number_of_days = (next_row_date - new_row_date).days
        else:
            if i < len(combined_docs) - 1:
                next_row_date = combined_docs[i + 1]['creation'].date()
                new_row.number_of_days = (next_row_date - new_row_date).days
            else:
                new_row.number_of_days = (end_date_inv - new_row_date).days + 1



        cur_recv_items = []
        if new_row.received_items:
            cur_recv_items = new_row.received_items.split('\n') if new_row.received_items else []
        
        cur_out_items = []
        if new_row.out_items:
            cur_out_items = new_row.out_items.split('\n') if new_row.out_items else []

        final_sto_itm = prev_sto_itm.copy()
        final_sto_itm.extend(cur_recv_items)

        final_sto_itm = [item for item in final_sto_itm if item not in cur_out_items]
        final_sto_itm = sorted(final_sto_itm, key=lambda x: int(x.replace('SN', '')))
        new_row.final_stored_items = '\n'.join(final_sto_itm) if final_sto_itm else ''

        prev_sto_itm = final_sto_itm

        # Default to 0 if rates are None
        new_row.daily_rate_withrim = float(doc.custom_charges_with_rim or 0)
        new_row.daily_rate_withoutrim = float(doc.custom_charges_without_rim or 0)

        new_row.daily_sub_total_withrim = new_row.final_qty_withrim * new_row.daily_rate_withrim
        new_row.daily_sub_total_withoutrim = new_row.final_qty_withoutrim * new_row.daily_rate_withoutrim
        
        new_row.cost_for_the_days_withrim = new_row.number_of_days * new_row.daily_sub_total_withrim
        new_row.cost_for_the_days_withoutrim = new_row.number_of_days * new_row.daily_sub_total_withoutrim
        
        new_row.amount = new_row.cost_for_the_days_withrim + new_row.cost_for_the_days_withoutrim

        previous_row_date = new_row.date

    total_amount = sum(float(row.amount or 0) for row in doc.custom_storage_fees_for_itemsth)
    minimum_threshold_charges_th(doc, total_amount, method = None)
    doc.custom_total_cost = total_amount
    # doc.custom_grand_total_cost = total_amount
    # doc.custom_total_in_words = frappe.utils.money_in_words(total_amount)





@frappe.whitelist(allow_guest=True)
def populate_subsequent_th_invoice_rows(doc, last_row, bill_of_landings, pick_lists):
    pick_list_map = {}
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        pl_date = pl_doc.custom_submission_datetime.date()
        if pl_date not in pick_list_map:
            pick_list_map[pl_date] = []
        pick_list_map[pl_date].append(pl_doc)

    bill_of_landing_map = {}
    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        bl_date = bl_doc.submission_datetime.date()
        if bl_date not in bill_of_landing_map:
            bill_of_landing_map[bl_date] = []
        bill_of_landing_map[bl_date].append(bl_doc)

    used_bill_of_landings = set()
    used_pick_lists = set()
    combined_docs = []

    # Add Bill of Landings to combined documents
    for bl in bill_of_landings:
        bl_doc = frappe.get_doc('Bill Of Landing', bl['name'])
        if bl_doc.name not in used_bill_of_landings:
            # Default to 0 if values are None
            received_qty_withrim = float(bl_doc.total_tyres_with_rim or 0)
            received_qty_withoutrim = float(bl_doc.total_tyres_without_rim or 0)
            combined_docs.append({
                'type': 'Bill Of Landing',
                'doc': bl_doc,
                'creation': bl_doc.submission_datetime,
                'received_qty_withrim': received_qty_withrim,
                'received_qty_withoutrim': received_qty_withoutrim,
                'received_items': bl_doc.all_item_serial_no,
                'out_items': None,
                'sold_qty_withrim': 0,
                'sold_qty_withoutrim': 0
            })
            used_bill_of_landings.add(bl_doc.name)

    # Add Pick Lists to combined documents
    for pl in pick_lists:
        pl_doc = frappe.get_doc('Pick List', pl['name'])
        if pl_doc.name not in used_pick_lists:
            # Default to 0 if values are None
            item_qty = float(pl_doc.custom_item_qty or 0)
            sold_qty_withrim = item_qty if pl_doc.custom_item_type == "with rim" else 0
            sold_qty_withoutrim = item_qty if pl_doc.custom_item_type == "without rim" else 0
            combined_docs.append({
                'type': 'Pick List',
                'doc': pl_doc,
                'creation': pl_doc.custom_submission_datetime,
                'sold_qty_withrim': sold_qty_withrim,
                'sold_qty_withoutrim': sold_qty_withoutrim,
                'received_items': None,
                'out_items': pl_doc.custom_all_item_serial_no_out,
                'received_qty_withrim': 0,
                'received_qty_withoutrim': 0
            })
            used_pick_lists.add(pl_doc.name)

    # Sort combined documents by submission datetime
    combined_docs.sort(key=lambda x: x['creation'])

    # Initialize running quantities from the last invoice's final quantities
    running_final_qty_withrim = float(last_row.final_qty_withrim or 0)
    running_final_qty_withoutrim = float(last_row.final_qty_withoutrim or 0)
    prev_sto_itm = last_row.final_stored_items.split('\n') if last_row.final_stored_items else []

    # Add the first row with the start date of the current invoice
    first_row = doc.append('custom_storage_fees_for_itemsth', {})
    first_row.date = frappe.utils.getdate(doc.custom_start_date_for_storage_cost_)
    first_row.final_qty_withrim = running_final_qty_withrim
    first_row.final_qty_withoutrim = running_final_qty_withoutrim
    first_row.received_qty_withrim = 0
    first_row.received_qty_withoutrim = 0
    first_row.sold_qty_withrim = 0
    first_row.sold_qty_withoutrim = 0
    first_row.final_stored_items = prev_sto_itm
    first_row.received_items = ""
    first_row.out_items = ""

    # Calculate number of days for the first row
    if combined_docs:
        next_row_date = combined_docs[0]['creation'].date()
    else:
        next_row_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
    
    first_row.number_of_days = (next_row_date - first_row.date).days

    # Calculate costs for the first row
    first_row.daily_rate_withrim = float(doc.custom_charges_with_rim or 0)
    first_row.daily_rate_withoutrim = float(doc.custom_charges_without_rim or 0)
    
    first_row.daily_sub_total_withrim = first_row.final_qty_withrim * first_row.daily_rate_withrim
    first_row.daily_sub_total_withoutrim = first_row.final_qty_withoutrim * first_row.daily_rate_withoutrim
    
    first_row.cost_for_the_days_withrim = first_row.number_of_days * first_row.daily_sub_total_withrim
    first_row.cost_for_the_days_withoutrim = first_row.number_of_days * first_row.daily_sub_total_withoutrim
    
    first_row.amount = first_row.cost_for_the_days_withrim + first_row.cost_for_the_days_withoutrim

    # Process the rest of the documents
    for i, doc_entry in enumerate(combined_docs):
        new_row = doc.append('custom_storage_fees_for_itemsth', {})
        new_row.date = doc_entry['creation'].date()

        if doc_entry['type'] == 'Bill Of Landing':
            new_row.bill_of_landing = doc_entry['doc'].name
            new_row.received_qty_withrim = float(doc_entry['received_qty_withrim'] or 0)
            new_row.received_qty_withoutrim = float(doc_entry['received_qty_withoutrim'] or 0)
            new_row.received_items = doc_entry['doc'].all_item_serial_no
            new_row.out_items = ""

            matching_pick_lists = pick_list_map.get(new_row.date, [])
            used_matching_pick_lists = [
                pl for pl in matching_pick_lists
                if pl.name not in used_pick_lists
            ]
            if used_matching_pick_lists:
                pl_doc = used_matching_pick_lists[0]
                # Default to 0 if values are None
                item_qty = float(pl_doc.custom_item_qty or 0)
                new_row.pick_list = pl_doc.name
                new_row.sold_qty_withrim = item_qty if pl_doc.custom_item_type == "With Rim" else 0
                new_row.sold_qty_withoutrim = item_qty if pl_doc.custom_item_type == "Without Rim" else 0
                used_pick_lists.add(pl_doc.name)
            else:
                new_row.sold_qty_withrim = 0
                new_row.sold_qty_withoutrim = 0

        else:  # Pick List
            new_row.pick_list = doc_entry['doc'].name
            new_row.sold_qty_withrim = float(doc_entry['sold_qty_withrim'] or 0)
            new_row.sold_qty_withoutrim = float(doc_entry['sold_qty_withoutrim'] or 0)
            new_row.received_items = ""
            new_row.out_items = doc_entry['doc'].custom_all_item_serial_no_out

            matching_bill_of_landings = bill_of_landing_map.get(new_row.date, [])
            used_matching_bill_of_landings = [
                bl for bl in matching_bill_of_landings
                if bl.name not in used_bill_of_landings
            ]
            if used_matching_bill_of_landings:
                bl_doc = used_matching_bill_of_landings[0]
                new_row.bill_of_landing = bl_doc.name
                # Default to 0 if values are None
                new_row.received_qty_withrim = float(bl_doc.total_tyres_with_rim or 0)
                new_row.received_qty_withoutrim = float(bl_doc.total_tyres_without_rim or 0)
                used_bill_of_landings.add(bl_doc.name)
            else:
                new_row.received_qty_withrim = 0
                new_row.received_qty_withoutrim = 0

        # Calculate running final quantities, ensuring float values and handling None
        received_withrim = float(new_row.received_qty_withrim or 0)
        received_withoutrim = float(new_row.received_qty_withoutrim or 0)
        sold_withrim = float(new_row.sold_qty_withrim or 0)
        sold_withoutrim = float(new_row.sold_qty_withoutrim or 0)

        running_final_qty_withrim += received_withrim - sold_withrim
        running_final_qty_withoutrim += received_withoutrim - sold_withoutrim
        
        new_row.final_qty_withrim = running_final_qty_withrim
        new_row.final_qty_withoutrim = running_final_qty_withoutrim

        # Calculate number of days
        if i < len(combined_docs) - 1:
            next_row_date = combined_docs[i + 1]['creation'].date()
        else:
            next_row_date = frappe.utils.getdate(doc.custom_end_date_for_storage_cost)
        
        new_row.number_of_days = (next_row_date - new_row.date).days + 1

        cur_recv_items = []
        if new_row.received_items:
            cur_recv_items = new_row.received_items.split('\n') if new_row.received_items else []
        
        cur_out_items = []
        if new_row.out_items:
            cur_out_items = new_row.out_items.split('\n') if new_row.out_items else []

        final_sto_itm = prev_sto_itm.copy()
        final_sto_itm.extend(cur_recv_items)

        final_sto_itm = [item for item in final_sto_itm if item not in cur_out_items]
        final_sto_itm = sorted(final_sto_itm, key=lambda x: int(x.replace('SN', '')))
        new_row.final_stored_items = '\n'.join(final_sto_itm) if final_sto_itm else ''

        prev_sto_itm = final_sto_itm

        # Set daily rates and calculate costs
        new_row.daily_rate_withrim = float(doc.custom_charges_with_rim or 0)
        new_row.daily_rate_withoutrim = float(doc.custom_charges_without_rim or 0)
        
        new_row.daily_sub_total_withrim = new_row.final_qty_withrim * new_row.daily_rate_withrim
        new_row.daily_sub_total_withoutrim = new_row.final_qty_withoutrim * new_row.daily_rate_withoutrim
        
        new_row.cost_for_the_days_withrim = new_row.number_of_days * new_row.daily_sub_total_withrim
        new_row.cost_for_the_days_withoutrim = new_row.number_of_days * new_row.daily_sub_total_withoutrim
        
        new_row.amount = new_row.cost_for_the_days_withrim + new_row.cost_for_the_days_withoutrim

    # Calculate total amount for the invoice, handling None values
    total_amount = sum(float(row.amount or 0) for row in doc.custom_storage_fees_for_itemsth)
    doc.custom_total_cost = total_amount
    minimum_threshold_charges_th(doc, total_amount, method = None)
    # doc.custom_grand_total_cost = total_amount
    # doc.custom_total_in_words = frappe.utils.money_in_words(total_amount)
    





def minimum_threshold_charges_th(doc, total_amount, method):
    storage_fees_rows = [row for row in doc.get("custom_storage_fees_for_itemsth")
                        if row.get("pick_list")]
    
    # Clear existing entries in custom_threshold_costth to avoid duplicates
    doc.set("custom_threshold_costth", [])
    
    total_threshold_cost = 0  # Initialize total cost
    
    for row in storage_fees_rows:
        pick_list = row.get("pick_list")
        date = row.get("date")
        out_items = row.get("out_items") or ""
        
        # Split the out_items text field to get individual serial numbers
        serial_numbers = [sn.strip() for sn in out_items.split('\n') if sn.strip()]
        
        # Create entries in custom_threshold_costth for each serial number
        for serial_no in serial_numbers:
            sn_doc = frappe.get_doc("Serial No", serial_no)
            date_received = sn_doc.creation.date()
            
            # Calculate total number of days stored
            total_days = (date - date_received).days
            
            # Calculate must be paid days
            must_be_paid_days = doc.custom_minimum_threshold_days - total_days
            
            # Calculate amount based on tyre type
            amount = 0
            if sn_doc.custom_tyre_type == "With Rim":
                amount = must_be_paid_days * doc.custom_charges_with_rim
            elif sn_doc.custom_tyre_type == "Without Rim":
                amount = must_be_paid_days * doc.custom_charges_without_rim
            
            # Add to total threshold cost
            total_threshold_cost += amount
            
            doc.append("custom_threshold_costth", {
                "item_serial_no": serial_no,
                "pick_list": pick_list,
                "date_out": date,
                "bill_of_landing": sn_doc.custom_creation_document_name,
                "date_received": date_received,
                "tyre_type": sn_doc.custom_tyre_type,
                "minimum_threshold_days": doc.custom_minimum_threshold_days,
                "charges_for_without_rim": doc.custom_charges_without_rim,
                "charges_for_with_rim": doc.custom_charges_with_rim,
                "total_number_of_days_stored": total_days,
                "must_be_paid_for_the_days": must_be_paid_days,
                "amount": amount
            })
    
    # Set the total threshold cost
    doc.custom_total_threshold_cost = float(total_threshold_cost)
    storagee_cost = float(total_amount or 0)
    total_cost = total_threshold_cost + storagee_cost
    doc.custom_grand_total_cost = total_cost
    doc.custom_total_in_words = frappe.utils.money_in_words(total_cost)















def on_submit_total(doc,method=None):
    if doc.custom_peneus_hub:
        total_amount = sum(row.amount for row in doc.custom_storage_fees_for_items)
        doc.custom_total_cost = total_amount
        doc.custom_grand_total_cost = total_amount
        doc.custom_total_in_words = frappe.utils.money_in_words(total_amount)
    elif doc.custom_tyre_hotel:
        threshold_cost = doc.custom_total_threshold_cost
        storagee_cost = doc.custom_total_cost
        total_cost = threshold_cost + storagee_cost
        doc.custom_total_cost = storagee_cost
        doc.custom_grand_total_cost = total_cost
        doc.custom_total_in_words = frappe.utils.money_in_words(total_cost)

    
    doc.status = "Submitted"
    doc.db_update()



def status_change_on_cancel(doc, method=None):
    doc.status = "Cancelled"
    doc.db_update()


def validate_dates(doc, method):
    if doc.custom_start_date_for_storage_cost_ and doc.custom_end_date_for_storage_cost and doc.posting_date:
        if doc.custom_start_date_for_storage_cost_ > doc.custom_end_date_for_storage_cost:
            frappe.throw(_("Start Date must be earlier than End Date."))
        if doc.custom_end_date_for_storage_cost > doc.posting_date:
            frappe.throw(_("End Date must be earlier than the Posting Date."))