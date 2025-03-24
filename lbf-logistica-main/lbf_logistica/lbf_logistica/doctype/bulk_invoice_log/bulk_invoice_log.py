# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, now



class BulkInvoiceLog(Document):
	def before_save(self):
		if self.service == "Peneus Hub":
			self.naming_series = "PH-BL-.YYYY.-.MM.-"

		elif self.service == "Tyre Hotel":
			self.naming_series = "TH-BL-.YYYY.-.MM.-"



	def before_submit(self):
		
		start_date = self.start_date_for_storage_cost
		end_date = self.end_date_for_storage_cost
		due_date = self.payment_due_date
		
		if self.service == "Peneus Hub":
			for customer in self.customer_details:
				invoice = frappe.get_doc({
					"doctype": "Sales Invoice",
					"customer": customer.customer,
					"custom_peneus_hub": 1,
					"custom_start_date_for_storage_cost_": start_date,
					"custom_end_date_for_storage_cost": end_date,
					"due_date": due_date,
					"custom_bulk_invoice_id": self.name


				})
				invoice.save()
				customer.invoice_id = invoice.name

		elif self.service == "Tyre Hotel":
			for customer in self.customer_details:
				invoice = frappe.get_doc({
					"doctype": "Sales Invoice",
					"customer": customer.customer,
					"custom_tyre_hotel": 1,
					"custom_start_date_for_storage_cost_": start_date,
					"custom_end_date_for_storage_cost": end_date,
					"due_date": due_date,
					"custom_bulk_invoice_id": self.name


				})
				invoice.save()
				customer.invoice_id = invoice.name

		







@frappe.whitelist()
def submit_invoices(docname):
	"""Submit all Sales Invoices linked in customer_details table."""
	try:
		doc = frappe.get_doc("Bulk Invoice Log", docname)  # Replace with your actual Doctype
		invoice_ids = [row.invoice_id for row in doc.customer_details if row.invoice_id]

		if not invoice_ids:
			frappe.msgprint("No invoices to submit.", alert=True)
			return

		submitted_count = 0
		for invoice_id in doc.customer_details:
			invoice = frappe.get_doc("Sales Invoice", invoice_id.invoice_id)
			if invoice.docstatus == 0 and invoice.custom_grand_total_cost != 0:  # Only submit if it's in draft state
				invoice.submit()
				submitted_count += 1

				invoice_id.invoice_submitted = 1
		doc.save()

		frappe.msgprint(f"Successfully submitted {submitted_count} invoices.")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Submit Invoices Error")
		frappe.throw(f"Error submitting invoices: {str(e)}")


