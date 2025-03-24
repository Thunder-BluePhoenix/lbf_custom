# Copyright (c) 2024, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, now
from lbf_logistica.overrides.serialno_barcode import before_save_serial, generate_document_barcode

class BillOfLanding(Document):
    def before_submit(self):
        self.submission_datetime = now_datetime()
        self.submission_date = now()
        if self.service == "Peneus Hub" and not self.legal_doc_for_redelivery:
            # Check for missing quality inspections
            missing_items = [item.item_name or item.item_code for item in self.item_details_ph if not item.quality_inspection_done]
            if missing_items:
                frappe.throw(
                    f"Quality Inspection must be completed for all items before submitting. Missing for Items: {', '.join(missing_items)}"
                )

            # Validate Pricing Rules
            pr_docs = frappe.get_all(
                "Pricing Rule",
                filters={"custom_customerr": self.customer},
            )
            if not pr_docs:
                frappe.throw(f"No Pricing Rule found for Customer: {self.customer}")

            # Serial and Batch Number Generation for accepted and rejected quantities
            for item in self.item_details_ph:
                item_doc = frappe.get_doc("Item", item.item_code)

                # Process Accepted Quantity
                if int(item.accepted_qty or 0) > 0:
                    if item_doc.has_batch_no:
                        batch_no = frappe.model.naming.make_autoname(item_doc.batch_number_series or "BATCH-.#####")
                        batch = frappe.get_doc({
                            "doctype": "Batch",
                            "batch_id": batch_no,
                            "item": item.item_code,
                            "batch_qty": item.accepted_qty,
                            "warehouse": self.accepted_warehouse,
                            "reference_doctype": "Bill Of Landing",
                            "reference_name": self.name,
                            "use_batchwise_valuation": 1
                        })
                        batch.flags.ignore_validate = True
                        batch.flags.ignore_permissions = True
                        batch.insert()
                        item.batch_no = batch_no

                    if item_doc.has_serial_no:
                        serial_nos = []
                        for i in range(int(item.accepted_qty or 0)):
                            serial_no = frappe.model.naming.make_autoname(item_doc.serial_no_series or "SERIAL-.#####")
                            serial_nos.append(serial_no)

                            custom_fields = {
                                "custom_tire_widthmm": item_doc.custom_tire_widthmm,
                                "custom_aspect_ratio": item_doc.custom_aspect_ratio,
                                "custom_carcass": item_doc.custom_carcass,
                                "custom_diameterinch": item_doc.custom_diameterinch,
                                "custom_load_index": item_doc.custom_load_index,
                                "custom_speed_rating": item_doc.custom_speed_rating,
                                "custom_weight": item_doc.custom_weight,
                                "custom_model": item_doc.custom_model,
                                "custom_marks": item_doc.custom_marks,
                                "brand": item_doc.brand
                            }

                            serial = frappe.get_doc({
                                "doctype": "Serial No",
                                "serial_no": serial_no,
                                "item_code": item.item_code,
                                "batch_no": item.batch_no or "",
                                "warehouse": self.accepted_warehouse,
                                "custom_creation_reference_doctype": "Bill Of Landing",
                                "custom_creation_document_name": self.name,
                                "status": "Active",
                                "custom_service": self.service,
                                "custom_customer": self.customer,
                                **custom_fields
                            })
                            serial.flags.ignore_validate = True
                            serial.flags.ignore_permissions = True
                            before_save_serial(serial, method=None)
                            serial.save()
                        item.serial_no = "\n".join(serial_nos)

                # Process Rejected Quantity
                # if int(item.rejected_qty or 0) > 0:
                #     if item_doc.has_batch_no:
                #         batch_no = frappe.model.naming.make_autoname(item_doc.batch_number_series or "BATCH-REJ-.#####")
                #         batch_rejected = frappe.get_doc({
                #             "doctype": "Batch",
                #             "batch_id": batch_no,
                #             "item": item.item_code,
                #             "batch_qty": item.rejected_qty,
                #             "warehouse": self.rejected_warehouse,
                #             "reference_doctype": "Bill Of Landing",
                #             "reference_name": self.name,
                #             "use_batchwise_valuation": 1,
                #             "disabled":1
                #         })
                #         batch_rejected.flags.ignore_validate = True
                #         batch_rejected.flags.ignore_permissions = True
                #         batch_rejected.insert()
                #         item.rejected_batch_no = batch_no

                #     if item_doc.has_serial_no:
                #         serial_nos_rejected = []
                #         for i in range(int(item.rejected_qty or 0)):
                #             serial_no = frappe.model.naming.make_autoname(item_doc.serial_no_series or "SERIAL-REJ-.#####")
                #             serial_nos_rejected.append(serial_no)

                #             custom_fields = {
                #                 "custom_tire_widthmm": item_doc.custom_tire_widthmm,
                #                 "custom_aspect_ratio": item_doc.custom_aspect_ratio,
                #                 "custom_carcass": item_doc.custom_carcass,
                #                 "custom_diameterinch": item_doc.custom_diameterinch,
                #                 "custom_load_index": item_doc.custom_load_index,
                #                 "custom_speed_rating": item_doc.custom_speed_rating,
                #                 "custom_weight": item_doc.custom_weight,
                #                 "custom_model": item_doc.custom_model,
                #                 "custom_marks": item_doc.custom_marks,
                #                 "brand": item_doc.brand
                #             }

                #             serial = frappe.get_doc({
                #                 "doctype": "Serial No",
                #                 "serial_no": serial_no,
                #                 "item_code": item.item_code,
                #                 "batch_no": item.rejected_batch_no or "",
                #                 "warehouse": self.rejected_warehouse,
                #                 "custom_creation_reference_doctype": "Bill Of Landing",
                #                 "custom_creation_document_name": self.name,
                #                 "status": "Inactive",
                #                 "custom_service": self.service,
                #                 "custom_customer": self.customer,
                #                 **custom_fields
                #             })
                #             serial.flags.ignore_validate = True
                #             serial.flags.ignore_permissions = True
                #             before_save_serial(serial, method=None)
                #             serial.save()
                #         item.rejected_serial_no = "\n".join(serial_nos_rejected)

                # Create Serial and Batch Bundle for both accepted and rejected quantities
                self.create_serial_and_batch_bundle(item)


            all_serial_no = []
            for item in self.item_details_ph:
                if item.serial_no:
                    all_serial_no.extend(item.serial_no.split('\n'))

            sorted_serial_no = sorted(all_serial_no, key=lambda x: int(x.replace('SN', '')))
            self.all_item_serial_no = '\n'.join(sorted_serial_no)
            self.status = "Closed"



        elif self.service == "Tyre Hotel" and not self.legal_doc_for_redelivery:


            # Check for missing quality inspections
            missing_items = [item.item_name or item.item_code for item in self.item_details_th if not item.done_quality_inspection]
            if missing_items:
                frappe.throw(
                    f"Quality Inspection must be completed for all items before submitting. Missing for Items: {', '.join(missing_items)}"
                )

            if not self.accepted_warehouse :
                frappe.throw("Please select an accepted warehouse")


            
            # Serial and Batch Number Generation for accepted and rejected quantities
            for item in self.item_details_th:
                if not item.customer_batch_bundle:
                    item_doc = frappe.get_doc("Item", item.item_code)
                    item.accepted_qty = item.qty

                    # Process Accepted Quantity
                    if int(item.accepted_qty or 0) > 0:
                        if item_doc.has_batch_no:
                            batch_no = frappe.model.naming.make_autoname(item_doc.batch_number_series or "BATCH-.#####")
                            batch = frappe.get_doc({
                                "doctype": "Batch",
                                "batch_id": batch_no,
                                "item": item.item_code,
                                "batch_qty": item.accepted_qty,
                                "warehouse": self.accepted_warehouse,
                                "reference_doctype": "Bill Of Landing",
                                "reference_name": self.name,
                                "use_batchwise_valuation": 1
                            })
                            batch.flags.ignore_validate = True
                            batch.flags.ignore_permissions = True
                            batch.insert()
                            item.batch_no = batch_no

                        if item_doc.has_serial_no:
                            serial_nos = []
                            for i in range(int(item.accepted_qty or 0)):
                                serial_no = frappe.model.naming.make_autoname(item_doc.serial_no_series or "SERIAL-.#####")
                                serial_nos.append(serial_no)

                                custom_fields = {
                                    "custom_tire_widthmm": item_doc.custom_tire_widthmm,
                                    "custom_aspect_ratio": item_doc.custom_aspect_ratio,
                                    "custom_carcass": item_doc.custom_carcass,
                                    "custom_diameterinch": item_doc.custom_diameterinch,
                                    "custom_load_index": item_doc.custom_load_index,
                                    "custom_speed_rating": item_doc.custom_speed_rating,
                                    "custom_weight": item_doc.custom_weight,
                                    "custom_model": item_doc.custom_model,
                                    "custom_marks": item_doc.custom_marks,
                                    "brand": item_doc.brand
                                }

                                serial = frappe.get_doc({
                                    "doctype": "Serial No",
                                    "serial_no": serial_no,
                                    "item_code": item.item_code,
                                    "batch_no": item.batch_no or "",
                                    "warehouse": self.accepted_warehouse,
                                    "custom_creation_reference_doctype": "Bill Of Landing",
                                    "custom_creation_document_name": self.name,
                                    "status": "Active",
                                    "custom_service": self.service,
                                    "custom_customer": self.customer,
                                    "custom_tyre_type": item.tyre_type,
                                    **custom_fields
                                })
                                serial.flags.ignore_validate = True
                                serial.flags.ignore_permissions = True
                                before_save_serial(serial, method=None)
                                serial.save()
                            item.serial_no = "\n".join(serial_nos)

                    

                            

                    # Process Rejected Quantity
                    # if int(item.rejected_qty or 0) > 0:
                    #     if item_doc.has_batch_no:
                    #         batch_no = frappe.model.naming.make_autoname(item_doc.batch_number_series or "BATCH-REJ-.#####")
                    #         batch_rejected = frappe.get_doc({
                    #             "doctype": "Batch",
                    #             "batch_id": batch_no,
                    #             "item": item.item_code,
                    #             "batch_qty": item.rejected_qty,
                    #             "warehouse": self.rejected_warehouse,
                    #             "reference_doctype": "Bill Of Landing",
                    #             "reference_name": self.name,
                    #             "use_batchwise_valuation": 1,
                    #             "disabled": 1
                    #         })
                    #         batch_rejected.flags.ignore_validate = True
                    #         batch_rejected.flags.ignore_permissions = True
                    #         batch_rejected.insert()
                    #         item.rejected_batch_no = batch_no

                    #     if item_doc.has_serial_no:
                    #         serial_nos_rejected = []
                    #         for i in range(int(item.rejected_qty or 0)):
                    #             serial_no = frappe.model.naming.make_autoname(item_doc.serial_no_series or "SERIAL-REJ-.#####")
                    #             serial_nos_rejected.append(serial_no)

                    #             custom_fields = {
                    #                 "custom_tire_widthmm": item_doc.custom_tire_widthmm,
                    #                 "custom_aspect_ratio": item_doc.custom_aspect_ratio,
                    #                 "custom_carcass": item_doc.custom_carcass,
                    #                 "custom_diameterinch": item_doc.custom_diameterinch,
                    #                 "custom_load_index": item_doc.custom_load_index,
                    #                 "custom_speed_rating": item_doc.custom_speed_rating,
                    #                 "custom_weight": item_doc.custom_weight,
                    #                 "custom_model": item_doc.custom_model,
                    #                 "custom_marks": item_doc.custom_marks,
                    #                 "brand": item_doc.brand
                    #             }

                    #             serial = frappe.get_doc({
                    #                 "doctype": "Serial No",
                    #                 "serial_no": serial_no,
                    #                 "item_code": item.item_code,
                    #                 "batch_no": item.rejected_batch_no or "",
                    #                 "warehouse": self.rejected_warehouse,
                    #                 "custom_creation_reference_doctype": "Bill Of Landing",
                    #                 "custom_creation_document_name": self.name,
                    #                 "status": "Inactive",
                    #                 "custom_service": self.service,
                    #                 "custom_customer": self.customer,
                    #                 **custom_fields
                    #             })
                    #             serial.flags.ignore_validate = True
                    #             serial.flags.ignore_permissions = True
                    #             before_save_serial(serial, method=None)
                    #             serial.save()
                    #         item.rejected_serial_no = "\n".join(serial_nos_rejected)

                    # Create Serial and Batch Bundle for both accepted and rejected quantities
                    self.create_serial_and_batch_bundle(item)

                else:
                    bundle_doc_accepted = item.serial_and_batch_bundle_accepted
                    
                    accepted_serials = item.serial_no.split("\n") 
                    for serial_no in accepted_serials:
                        serial_no = serial_no.strip()  # Remove any leading/trailing whitespace
                        
                        if serial_no:  # Ensure serial_no is not empty
                            serial_doc = frappe.get_doc("Serial No", serial_no)
                            serial_doc.warehouse = self.accepted_warehouse  # Update status
                            serial_doc.flags.ignore_validate = True
                            serial_doc.flags.ignore_permissions = True
                            serial_doc.save() 


                    



                    self.create_serial_and_batch_bundle(item)



            all_serial_no = []
            for item in self.item_details_th:
                if item.serial_no:
                    all_serial_no.extend(item.serial_no.split('\n'))

            sorted_serial_no = sorted(all_serial_no, key=lambda x: int(x.replace('SN', '')))
            self.all_item_serial_no = '\n'.join(sorted_serial_no)
            self.status = "Closed"





    def validate(self, method=None):
    # Update total quantities
        self.total_qty = sum(int(item.total_qty or 0) for item in self.item_details_ph)
        self.total_qty_th = sum(int(item.qty or 0) for item in self.item_details_th)
        self.total_qty_accepted = sum(int(item.accepted_qty or 0) for item in self.item_details_ph)
        self.total_qty_rejected = sum(int(item.rejected_qty or 0) for item in self.item_details_ph)


        # Update handling_in_charges table
        for handling_in in self.handling_in_charges:
            for item in self.item_details_ph:
                if handling_in.item_code == item.item_code:
                    handling_in.accepted_qty = flt(item.accepted_qty or 0)
                    handling_in.amount = flt(handling_in.rate or 0) * flt(item.accepted_qty or 0)

        # Update handling_out_charges table
        for handling_out in self.handling_out_charges:
            for item in self.item_details_ph:
                if handling_out.item_code == item.item_code:
                    handling_out.accepted_qty = flt(item.accepted_qty or 0)
                    handling_out.amount = flt(handling_out.rate or 0) * flt(item.accepted_qty or 0)
        


        update_bill_of_landing_charges(self, method)

    def before_save(self):
        if self.service == "Tyre Hotel":
            # self.naming_series ="MAT-PRE-TH-.YYYY.-.MM.-"
            customer = self.customer
            tyre_hotel_settings = frappe.get_doc("Tyre Hotel Pricing Rule", customer)

            self.th_charges = []
            total_tyres_with_rim = 0
            total_tyres_without_rim = 0

            for item in self.item_details_th:
                if item.tyre_type == "With Rim":
                    rate = flt(tyre_hotel_settings.amount_with_rim)
                    total_tyres_with_rim += int(item.accepted_qty or 0)
                elif item.tyre_type == "Without Rim":
                    rate = flt(tyre_hotel_settings.amount_without_rim)
                    total_tyres_without_rim += int(item.accepted_qty or 0)
                else:
                    frappe.throw(f"Invalid Tyre Type: {item.tyre_type} for Item: {item.item_code}")

                item.rate = rate
                item.amount = rate * flt(item.accepted_qty or 0)

                self.append("th_charges", {
                    "item_name": item.item_name,
                    "item_code": item.item_code,
                    "qty": item.accepted_qty or 0,
                    "tyre_type": item.tyre_type,
                    "rate": rate,
                    "amount": item.amount
                })
                self.total_tyres_with_rim = total_tyres_with_rim
                self.total_tyres_without_rim = total_tyres_without_rim
                self.total_qty_th = total_tyres_with_rim + total_tyres_without_rim
            
            

    def create_serial_and_batch_bundle(self, item):
        """
        Create separate Serial and Batch Bundles for accepted and rejected quantities of an item.
        """

        default_company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

        # Create Serial and Batch Bundle for Accepted Quantity
        if int(item.accepted_qty or 0) > 0:
            bundle_doc_accepted = frappe.new_doc("Serial and Batch Bundle")
            bundle_doc_accepted.item_code = item.item_code
            bundle_doc_accepted.item_name = item.item_name
            bundle_doc_accepted.company = default_company
            bundle_doc_accepted.warehouse = self.accepted_warehouse
            bundle_doc_accepted.type_of_transaction = "Inward"
            bundle_doc_accepted.voucher_type = "Bill Of Landing"
            bundle_doc_accepted.voucher_no = self.name
            bundle_doc_accepted.total_qty = flt(item.accepted_qty)
            bundle_doc_accepted.custom_is_active =1
            bundle_doc_accepted.custom_customer = self.customer

            valuation_rate = frappe.db.get_value("Item", item.item_code, "valuation_rate") or 0

            # Populate Serial and Batch Table for Accepted Quantity
            serial_nos_accepted = item.serial_no.split("\n") if item.serial_no else []
            for serial_no in serial_nos_accepted:
                serial_doc = frappe.get_doc("Serial No", serial_no)
                bundle_doc_accepted.append("entries", {
                    "serial_no": serial_no,
                    "batch_no": serial_doc.batch_no or "",
                    "qty": 1,
                    "warehouse": self.accepted_warehouse,
                    "valuation_rate": valuation_rate
                })

            bundle_doc_accepted.flags.ignore_mandatory = True
            bundle_doc_accepted.flags.ignore_validate = True
            bundle_doc_accepted.flags.ignore_permissions = True
            bundle_doc_accepted.insert()
            bundle_doc_accepted.submit()

            item.serial_and_batch_bundle_accepted = bundle_doc_accepted.name

            # Create Ledger Entry for Accepted Quantity
            self.create_ledger_entry(bundle_doc_accepted)

        # # Create Serial and Batch Bundle for Rejected Quantity
        # if int(item.rejected_qty or 0) > 0:
        #     bundle_doc_rejected = frappe.new_doc("Serial and Batch Bundle")
        #     bundle_doc_rejected.item_code = item.item_code
        #     bundle_doc_rejected.item_name = item.item_name
        #     bundle_doc_rejected.company = default_company
        #     bundle_doc_rejected.warehouse = self.rejected_warehouse
        #     bundle_doc_rejected.type_of_transaction = "Inward"
        #     bundle_doc_rejected.voucher_type = "Bill Of Landing"
        #     bundle_doc_rejected.voucher_no = self.name
        #     bundle_doc_rejected.total_qty = flt(item.rejected_qty)

        #     valuation_rate = frappe.db.get_value("Item", item.item_code, "valuation_rate") or 0

        #     # Populate Serial and Batch Table for Rejected Quantity
        #     serial_nos_rejected = item.rejected_serial_no.split("\n") if item.rejected_serial_no else []
        #     for serial_no in serial_nos_rejected:
        #         bundle_doc_rejected.append("entries", {
        #             "serial_no": serial_no,
        #             "batch_no": item.rejected_batch_no or "",
        #             "qty": 1,
        #             "warehouse": self.rejected_warehouse,
        #             "valuation_rate": valuation_rate
        #         })

        #     bundle_doc_rejected.flags.ignore_mandatory = True
        #     bundle_doc_rejected.flags.ignore_validate = True
        #     bundle_doc_rejected.flags.ignore_permissions = True
        #     bundle_doc_rejected.insert()
        #     bundle_doc_rejected.submit()

        #     item.serial_and_batch_bundle_rejected = bundle_doc_rejected.name

        #     # Create Ledger Entry for Rejected Quantity
        #     self.create_ledger_entry(bundle_doc_rejected)


    def create_ledger_entry(self, bundle_doc):
        """
        Create ledger entry for the submitted Serial and Batch Bundle
        """
        ledger_entry = frappe.new_doc("Stock Ledger Entry")
        ledger_entry.item_code = bundle_doc.item_code
        ledger_entry.warehouse = bundle_doc.warehouse
        ledger_entry.company = bundle_doc.company
        ledger_entry.voucher_type = bundle_doc.voucher_type
        ledger_entry.voucher_no = bundle_doc.voucher_no
        ledger_entry.serial_and_batch_bundle = bundle_doc.name  # Link the bundle
        ledger_entry.actual_qty = bundle_doc.total_qty
        ledger_entry.qty_change = bundle_doc.total_qty  # Matches total_qty
        ledger_entry.qty_after_transaction = bundle_doc.total_qty  # Assuming stock was zero before
        ledger_entry.incoming_rate = 0  # Adjust as necessary
        ledger_entry.valuation_rate = 0  # Adjust as necessary
        ledger_entry.balance_stock_value = 0  # Adjust as necessary
        ledger_entry.change_in_stock_value = 0  # Adjust as necessary
        ledger_entry.posting_date = frappe.utils.nowdate()
        ledger_entry.posting_time = frappe.utils.nowtime()
        ledger_entry.fiscal_year = frappe.defaults.get_user_default("fiscal_year")
        ledger_entry.auto_created_serial_and_batch_bundle = 1
        ledger_entry.flags.ignore_mandatory = True
        ledger_entry.flags.ignore_validate = True
        ledger_entry.flags.ignore_permissions = True
        ledger_entry.insert()
        ledger_entry.submit()


    def before_cancel(self, method):
        self.status = "Cancelled"



@frappe.whitelist()
def create_quality_inspections(bill_of_lading):
    bill_of_lading_doc = frappe.get_doc('Bill Of Landing', bill_of_lading)

    # Determine which table to fetch items from based on 'service' field
    if bill_of_lading_doc.service == "Peneus Hub":
        items_table = bill_of_lading_doc.item_details_ph  # Existing logic
        qty_field = "total_qty"
    elif bill_of_lading_doc.service == "Tyre Hotel":
        items_table = bill_of_lading_doc.item_details_th  # New logic
        qty_field = "qty"
    else:
        frappe.throw("Invalid service type. Expected 'Peneus Hub' or 'Tyre Hotel'.")

    if not items_table:
        frappe.throw("No items found in the respective item details table.")

    created_qis = []  

    # Iterate through the determined table
    if bill_of_lading_doc.service == "Peneus Hub":
        for item in items_table:
            existing_qi = frappe.db.exists(
                "Quality Inspection",
                {
                    "reference_type": "Bill Of Landing",
                    "reference_name": bill_of_lading_doc.name,
                    "item_code": item.item_code
                }
            )

            if not existing_qi:
                quality_inspection = frappe.new_doc('Quality Inspection')
                quality_inspection.item_code = item.item_code
                quality_inspection.reference_type = "Bill Of Landing"
                quality_inspection.reference_name = bill_of_lading_doc.name
                quality_inspection.inspection_type = "Incoming"
                quality_inspection.inspected_by = frappe.session.user
                quality_inspection.sample_size = getattr(item, qty_field)  # Dynamically fetch qty field
                quality_inspection.status = ""
                quality_inspection.custom_service = bill_of_lading_doc.service

                # Bypass mandatory validations and permissions
                quality_inspection.flags.ignore_mandatory = True
                quality_inspection.flags.ignore_validate = True
                quality_inspection.flags.ignore_permissions = True
                quality_inspection.flags.ignore_validate_update_after_submit = True
                quality_inspection.save(ignore_permissions=True)

                created_qis.append(quality_inspection.name)

    

    if bill_of_lading_doc.service == "Tyre Hotel":
        for item in items_table:
            existing_qi = frappe.db.exists(
                "Quality Inspection",
                {
                    "reference_type": "Bill Of Landing",
                    "reference_name": bill_of_lading_doc.name,
                    "item_code": item.item_code,
                    "custom_type": item.tyre_type
                }
            )

            if not existing_qi:
                quality_inspection = frappe.new_doc('Quality Inspection')
                quality_inspection.item_code = item.item_code
                quality_inspection.reference_type = "Bill Of Landing"
                quality_inspection.reference_name = bill_of_lading_doc.name
                quality_inspection.inspection_type = "Incoming"
                quality_inspection.inspected_by = frappe.session.user
                quality_inspection.sample_size = getattr(item, qty_field)  # Dynamically fetch qty field
                quality_inspection.custom_type = item.tyre_type
                quality_inspection.status = ""
                quality_inspection.custom_service = bill_of_lading_doc.service
                quality_inspection.custom_serial_and_batch_bundle_id = item.customer_batch_bundle

                # Bypass mandatory validations and permissions
                quality_inspection.flags.ignore_mandatory = True
                quality_inspection.flags.ignore_validate = True
                quality_inspection.flags.ignore_permissions = True
                quality_inspection.flags.ignore_validate_update_after_submit = True
                quality_inspection.save(ignore_permissions=True)

                created_qis.append(quality_inspection.name)

    bill_of_lading_doc.status = "Under QI"
    bill_of_lading_doc.save()

    return created_qis







@frappe.whitelist()
def update_bill_of_landing_charges(doc, method):
    # Fetch all Pricing Rule documents for the customer
    if doc.service == "Peneus Hub":
        pr_docs = frappe.get_all(
            "Pricing Rule",
            filters={"custom_customerr": doc.customer},
        )
        if not pr_docs:
            frappe.msgprint(f"No Pricing Rule found for Customer: {doc.customer}", alert=True)
            return

        pr_doc = frappe.get_doc("Pricing Rule", pr_docs[0])

        if pr_doc.apply_on == "Item Code":
            # Extract all item codes from the Pricing Rule items table
            pricing_rule_item_codes = [row.item_code for row in pr_doc.items]

            for item in doc.item_details_ph:
                # Check if the item_code exists in the Pricing Rule's items table
                if item.item_code in pricing_rule_item_codes:
                    # Handling IN Charges
                    if pr_doc.custom_handling_in:
                        # Check if the item already exists in handling_in_charges
                        exists_in = any(
                            row.item_code == item.item_code for row in doc.handling_in_charges
                        )
                        if not exists_in:
                            doc.append("handling_in_charges", {
                                "item_name": item.item_name,
                                "item_code": item.item_code,
                                "rate": flt(pr_doc.custom_amount_handling_in),
                                "accepted_qty": flt(item.accepted_qty),
                                "amount": flt(pr_doc.custom_amount_handling_in) * flt(item.accepted_qty)
                            })

                    # Handling OUT Charges
                    if pr_doc.custom_handling_out:
                        # Check if the item already exists in handling_out_charges
                        exists_out = any(
                            row.item_code == item.item_code for row in doc.handling_out_charges
                        )
                        if not exists_out:
                            doc.append("handling_out_charges", {
                                "item_name": item.item_name,
                                "item_code": item.item_code,
                                "rate": flt(pr_doc.custom_amount_handling_out),
                                "accepted_qty": flt(item.accepted_qty),
                                "amount": flt(pr_doc.custom_amount_handling_out) * flt(item.accepted_qty)
                            })

        elif pr_doc.apply_on == "Item Group":
            for item in doc.item_details_ph:
                # Fetch the item_group from the Item doctype
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                
                # Check if item_group matches the Pricing Rule's item groups
                if item_group in [row.item_group for row in pr_doc.item_groups]:
                    # Handling IN Charges
                    if pr_doc.custom_handling_in:
                        exists_in = any(
                            row.item_code == item.item_code for row in doc.handling_in_charges
                        )
                        if not exists_in:
                            doc.append("handling_in_charges", {
                                "item_name": item.item_name,
                                "item_code": item.item_code,
                                "rate": flt(pr_doc.custom_amount_handling_in),
                                "accepted_qty": flt(item.accepted_qty),
                                "amount": flt(pr_doc.custom_amount_handling_in) * flt(item.accepted_qty)
                            })

                    # Handling OUT Charges
                    if pr_doc.custom_handling_out:
                        exists_out = any(
                            row.item_code == item.item_code for row in doc.handling_out_charges
                        )
                        if not exists_out:
                            doc.append("handling_out_charges", {
                                "item_name": item.item_name,
                                "item_code": item.item_code,
                                "rate": flt(pr_doc.custom_amount_handling_out),
                                "accepted_qty": flt(item.accepted_qty),
                                "amount": flt(pr_doc.custom_amount_handling_out) * flt(item.accepted_qty)
                            })
        elif pr_doc.apply_on == "Brand":
            # Extract all brands from the Pricing Rule brands table
            pricing_rule_brands = [row.brand for row in pr_doc.brands]

            for item in doc.item_details_ph:
                # Fetch the brand from the Item doctype
                item_brand = frappe.db.get_value("Item", item.item_code, "brand")
                
                # Check if the brand matches the Pricing Rule's brands table
                if item_brand in pricing_rule_brands:
                    # Handling IN Charges
                    if pr_doc.custom_handling_in:
                        exists_in = any(
                            row.item_code == item.item_code for row in doc.handling_in_charges
                        )
                        if not exists_in:
                            doc.append("handling_in_charges", {
                                "item_name": item.item_name,
                                "item_code": item.item_code,
                                "rate": flt(pr_doc.custom_amount_handling_in),
                                "accepted_qty": flt(item.accepted_qty),
                                "amount": flt(pr_doc.custom_amount_handling_in) * flt(item.accepted_qty)
                            })

                    # Handling OUT Charges
                    if pr_doc.custom_handling_out:
                        exists_out = any(
                            row.item_code == item.item_code for row in doc.handling_out_charges
                        )
                        if not exists_out:
                            doc.append("handling_out_charges", {
                                "item_name": item.item_name,
                                "item_code": item.item_code,
                                "rate": flt(pr_doc.custom_amount_handling_out),
                                "accepted_qty": flt(item.accepted_qty),
                                "amount": flt(pr_doc.custom_amount_handling_out) * flt(item.accepted_qty)
                            })               









@frappe.whitelist()
def create_stock_entry(bill_of_landing):
    """
    Create Stock Entry documents for each Serial and Batch Bundle in the Bill of Lading.
    Fetches data from Serial No documents linked in the bundle entries.
    
    :param bill_of_lading: Name of the Bill of Lading document
    :return: List of created Stock Entry names
    """
    try:
        # Fetch the Bill of Lading document
        bol_doc = frappe.get_doc("Bill Of Landing", bill_of_landing)


        if bol_doc.service == "Peneus Hub":
        
            if not bol_doc.item_details_ph:
                frappe.throw(_("No items found in the Bill of Lading to create Stock Entry."))
                return []

            # List to store created Stock Entry names
            created_stock_entries = []

            # Iterate through item_details_ph table
            for item in bol_doc.item_details_ph:
                bundle_id = item.get("serial_and_batch_bundle_accepted")
                if not bundle_id:
                    frappe.msgprint(_("Skipping row {0}: No Serial and Batch Bundle found.").format(item.idx))
                    continue

                # Check if a Stock Entry already exists for this bundle and Bill of Lading
                # existing_se = frappe.get_all("Stock Entry", filters={
                #     "custom_serial_and_batch_bundle_id": bundle_id,
                #     "custom_bill_of_landing": bol_doc.name,  # Match the Bill of Lading
                #     "docstatus": ["!=", 2]  # Exclude cancelled documents
                # })
                # if existing_se:
                #     frappe.msgprint(_("Stock Entry already exists for Serial and Batch Bundle {0} and Bill of Lading {1}.")
                #                    .format(bundle_id, bol_doc.name))
                #     continue

                # Fetch the Serial and Batch Bundle document
                bundle_doc = frappe.get_doc("Serial and Batch Bundle", bundle_id)
                if not bundle_doc.entries:
                    frappe.msgprint(_("No entries found in Serial and Batch Bundle {0}. Skipping.").format(bundle_id))
                    continue

                # Create a new Stock Entry document
                stock_entry_doc = frappe.new_doc("Stock Entry")
                stock_entry_doc.stock_entry_type = "Material Transfer"
                stock_entry_doc.custom_serial_and_batch_bundle = bundle_id
                stock_entry_doc.custom_bill_of_landing = bol_doc.name

                # Populate items from bundle entries
                for entry in bundle_doc.entries:
                    try:
                        # Fetch the Serial No document
                        serial_no_doc = frappe.get_doc("Serial No", entry.serial_no)
                        
                        # Prepare item details from Serial No document
                        item_details = {
                            "item_code": serial_no_doc.item_code,
                            "s_warehouse": serial_no_doc.warehouse,
                            "t_warehouse": None,  # Leave blank or set a default if required
                            "qty": 1,  # Assuming 1 per serial no; adjust if needed
                            "uom": "Nos",  # Default UOM; fetch from item if needed
                            "custom_serial_noo": serial_no_doc.name,
                            "custom_batch_id": serial_no_doc.batch_no if hasattr(serial_no_doc, "batch_no") else None,
                            "allow_zero_valuation_rate": 1,
                            "actual_qty": 1,
                            "custom_serial_and_batch_bundle_id": bundle_id,
                            "custom_barcode_of_serial": serial_no_doc.custom_barcode if hasattr(serial_no_doc, "custom_barcode") else None
                        }

                        # Append item to Stock Entry
                        stock_entry_doc.append("items", item_details)

                    except frappe.DoesNotExistError:
                        frappe.log_error(f"Serial No {entry.serial_no} not found", "Stock Entry Creation Error")
                        frappe.msgprint(_("Serial No {0} not found in bundle {1}. Skipping.").format(entry.serial_no, bundle_id))
                        continue

                # Validate that items were added
                if not stock_entry_doc.items:
                    frappe.msgprint(_("No valid items added to Stock Entry for Serial and Batch Bundle {0}. Skipping.").format(bundle_id))
                    continue

                # Save and submit the Stock Entry
                stock_entry_doc.save()
                # stock_entry_doc.submit()
                created_stock_entries.append(stock_entry_doc.name)

                # Log success
                frappe.msgprint(_("Stock Entry {0} created successfully for Serial and Batch Bundle {1}.")
                                .format(stock_entry_doc.name, bundle_id))

            # Update the Bill of Lading to mark stock_entry_created as 1 if all bundles processed
            if created_stock_entries:
                frappe.db.set_value("Bill Of Landing", bol_doc.name, "stock_entry_created", 1)


        elif bol_doc.service == "Tyre Hotel":
            if not bol_doc.item_details_th:
                frappe.throw(_("No items found in the Bill of Lading to create Stock Entry."))
                return []

            # List to store created Stock Entry names
            created_stock_entries = []

            # Iterate through item_details_ph table
            for item in bol_doc.item_details_th:
                bundle_id = item.get("serial_and_batch_bundle_accepted")
                if not bundle_id:
                    frappe.msgprint(_("Skipping row {0}: No Serial and Batch Bundle found.").format(item.idx))
                    continue

                # Check if a Stock Entry already exists for this bundle and Bill of Lading
                # existing_se = frappe.get_all("Stock Entry", filters={
                #     "custom_serial_and_batch_bundle_id": bundle_id,
                #     "custom_bill_of_landing": bol_doc.name,  # Match the Bill of Lading
                #     "docstatus": ["!=", 2]  # Exclude cancelled documents
                # })
                # if existing_se:
                #     frappe.msgprint(_("Stock Entry already exists for Serial and Batch Bundle {0} and Bill of Lading {1}.")
                #                    .format(bundle_id, bol_doc.name))
                #     continue

                # Fetch the Serial and Batch Bundle document
                bundle_doc = frappe.get_doc("Serial and Batch Bundle", bundle_id)
                if not bundle_doc.entries:
                    frappe.msgprint(_("No entries found in Serial and Batch Bundle {0}. Skipping.").format(bundle_id))
                    continue

                # Create a new Stock Entry document
                stock_entry_doc = frappe.new_doc("Stock Entry")
                stock_entry_doc.stock_entry_type = "Material Transfer"
                stock_entry_doc.custom_serial_and_batch_bundle = bundle_id
                stock_entry_doc.custom_bill_of_landing = bol_doc.name

                # Populate items from bundle entries
                for entry in bundle_doc.entries:
                    try:
                        # Fetch the Serial No document
                        serial_no_doc = frappe.get_doc("Serial No", entry.serial_no)
                        
                        # Prepare item details from Serial No document
                        item_details = {
                            "item_code": serial_no_doc.item_code,
                            "s_warehouse": serial_no_doc.warehouse,
                            "t_warehouse": None,  # Leave blank or set a default if required
                            "qty": 1,  # Assuming 1 per serial no; adjust if needed
                            "uom": "Nos",  # Default UOM; fetch from item if needed
                            "custom_serial_noo": serial_no_doc.name,
                            "custom_batch_id": serial_no_doc.batch_no if hasattr(serial_no_doc, "batch_no") else None,
                            "allow_zero_valuation_rate": 1,
                            "actual_qty": 1,
                            "custom_serial_and_batch_bundle_id": bundle_id,
                            "custom_barcode_of_serial": serial_no_doc.custom_barcode if hasattr(serial_no_doc, "custom_barcode") else None
                        }

                        # Append item to Stock Entry
                        stock_entry_doc.append("items", item_details)

                    except frappe.DoesNotExistError:
                        frappe.log_error(f"Serial No {entry.serial_no} not found", "Stock Entry Creation Error")
                        frappe.msgprint(_("Serial No {0} not found in bundle {1}. Skipping.").format(entry.serial_no, bundle_id))
                        continue

                # Validate that items were added
                if not stock_entry_doc.items:
                    frappe.msgprint(_("No valid items added to Stock Entry for Serial and Batch Bundle {0}. Skipping.").format(bundle_id))
                    continue

                # Save and submit the Stock Entry
                stock_entry_doc.save()
                # stock_entry_doc.submit()
                created_stock_entries.append(stock_entry_doc.name)

                # Log success
                frappe.msgprint(_("Stock Entry {0} created successfully for Serial and Batch Bundle {1}.")
                                .format(stock_entry_doc.name, bundle_id))

            # Update the Bill of Lading to mark stock_entry_created as 1 if all bundles processed
            if created_stock_entries:
                frappe.db.set_value("Bill Of Landing", bol_doc.name, "stock_entry_created", 1)

        return created_stock_entries

    except Exception as e:
        frappe.log_error(f"Error creating Stock Entry from Bill of Landing {bill_of_landing}: {str(e)}", "Stock Entry Creation Error")
        frappe.throw(_("Failed to create Stock Entry: {0}").format(str(e)))
        return []






















# import frappe
# from frappe.utils import cint
# from werkzeug.wrappers import Response

# @frappe.whitelist(allow_guest=True)
# def generate_pnr(docname):
#     """
#     Generate a PNR file and directly trigger the download.
#     """
#     doc = frappe.get_doc("Bill Of Landing", docname)
    
#     # Determine the items list based on the service type
#     if doc.service == "Peneus Hub":
#         items = doc.item_details_ph
#     elif doc.service == "Tyre Hotel":
#         items = doc.item_details_th
#     else:
#         frappe.throw("Invalid service type.")

#     # Prepare PRN content
#     prn_lines = []

#     for row in items:
#         accepted_bundles = (row.serial_and_batch_bundle_accepted or "").split(",")

#         for bundle in accepted_bundles:
#             if not bundle.strip():
#                 continue
            
#             bundle_doc = frappe.get_doc("Serial and Batch Bundle", bundle.strip())
            
#             for entry in bundle_doc.entries:
#                 if not entry.serial_no:
#                     continue
                
#                 serial_doc = frappe.get_doc("Serial No", entry.serial_no.strip())

#                 # Generate PRN content based on service type
#                 if doc.service == "Tyre Hotel":
#                     prn_content = f"""%0H0160V0030B102040*{serial_doc.name}*
#                                     %0H0100V0070P02$A,024,024,0$={doc.customer or ''}
#                                     %0H0100V0083P02$A,090,090,0$={doc.plate or ''}
#                                     %0H0100V0168P02$A,024,024,0$=ORDER:
#                                     %0H0230V0156P02$A,044,044,0$={doc.name or ''}
#                                     %0H0350V0168P02$A,024,024,0$=DATED
#                                     %0H0400V0168P02$A,024,024,0$={doc.order_date or ''}
#                                     %0H0100V0193P02$A,024,024,0$=VEHICLE:
#                                     %0H0230V0193P02$A,024,024,0$={doc.vehicle or ''}
#                                     %0H0100V0218P02$A,024,024,0$=BRAND:
#                                     %0H0230V0218P02$A,024,024,0$={row.tyre_brand or ''}
#                                     %0H0100V0243P02$A,024,024,0$=MODEL:
#                                     %0H0230V0243P02$A,024,024,0$={row.tyre_model or ''}
#                                     %0H0100V0268P02$A,024,024,0$=SIZE:
#                                     %0H0230V0268P02$A,024,024,0$={row.tyre_size or ''}
#                                     %0H0100V0293P02$A,024,024,0$={row.season_kit_condition or ''}
#                                     %0H0160V0325B102040*{serial_doc.name}*
#                                     %0H0209V0370L0101P07XM*{serial_doc.name}*
#                                     %1H0600V0310P02$A,042,030,0$=PACKAGE {row.package_number or ''}/{row.package_total or ''}
#                                     /01
#                                     ~A0
#                                     Q1Z
#                                     """
#                 else:  # Peneus Hub (PH)
#                     prn_content = f"""%0H0120V0040P02$A,024,024,0$={row.h_line_0_1 or ''}
#                                     %0H0250V0040P02$A,024,024,0$={row.h_line_0_2 or ''}
#                                     %0H0120V0050P02$A,100,090,0$={doc.package_label or ''}
#                                     %0H0120V0130P02$A,024,024,0$={row.h_line_1_1 or ''}
#                                     %0H0250V0130P02$A,024,024,0$={row.h_line_1_2 or ''}
#                                     %0H0350V0130P02$A,024,024,0$={row.h_line_1_3 or ''}
#                                     %0H0450V0130P02$A,024,024,0$={row.h_line_1_4 or ''}
#                                     %0H0120V0155P02$A,024,024,0$={row.h_line_2_1 or ''}
#                                     %0H0250V0155P02$A,024,024,0$={row.h_line_2_2 or ''}
#                                     %0H0120V0180P02$A,024,024,0$={row.h_line_3_1 or ''}
#                                     %0H0250V0180P02$A,024,024,0$={row.h_line_3_2 or ''}
#                                     %0H0120V0205P02$A,024,024,0$={row.h_line_4_1 or ''}
#                                     %0H0250V0205P02$A,024,024,0$={row.h_line_4_2 or ''}
#                                     %0H0120V0315B102040*{serial_doc.custom_barcode or ''}*
#                                     %0H0169V0360L0101P07XM*{serial_doc.custom_barcode or ''}*
#                                     %1H0600V0300P02$A,042,030,0$={row.v_line_1 or ''}{row.v_line_2 or ''}
#                                     /01
#                                     ~A0
#                                     Q1Z
#                                     """

#                 prn_lines.append(prn_content)

#     # Combine all PRN data
#     prn_data = "\n".join(prn_lines)

#     # Return file as a direct download
#     frappe.local.response.filename = f"{docname}.prn"
#     frappe.local.response.filecontent = prn_data
#     frappe.local.response.type = "binary"





import os
import random
import string
import unicodedata
from io import BytesIO
import frappe


def generate_random_string(length=10):
   """Generate a random string for temporary file names"""
   return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def remove_accents(text):
   """Remove accents from text and replace special characters"""
   if isinstance(text, str):
       text = text.replace("°", ".")
       return ''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))
   return text


def generate_label_file(doc, items, service_type="Peneus Hub"):
   
   # Determine label templates based on service type
    app_path = frappe.get_app_path('lbf_logistica')

    if service_type == "Peneus Hub":
        header_template_path = os.path.join(app_path, 'public', 'templates', 'label_templates', 'label_header_ph.prn')
        body_template_path = os.path.join(app_path, 'public', 'templates', 'label_templates', 'label_body_ph.prn')
    else:  # Tyre Hotel
        header_template_path = os.path.join(app_path, 'public', 'templates', 'label_templates', 'label_header_th.prn')
        body_template_path = os.path.join(app_path, 'public', 'templates', 'label_templates', 'label_body_th.prn')


    # Read template files
    try:
        with open(header_template_path, 'rb') as f:
            header_template = f.read()

        with open(body_template_path, 'rb') as f:
            body_template = f.read()
    except FileNotFoundError as e:
        # Create directory structure if it doesn't exist
        template_dir = os.path.dirname(header_template_path)
        if not os.path.exists(template_dir):
            os.makedirs(template_dir, exist_ok=True)
        
        # Create default template files
        if service_type == "Peneus Hub":
            create_default_ph_templates(header_template_path, body_template_path)
        else:  # Tyre Hotel
            create_default_th_templates(header_template_path, body_template_path)
            
        # Try reading again
        with open(header_template_path, 'rb') as f:
            header_template = f.read()

        with open(body_template_path, 'rb') as f:
            body_template = f.read()



    # Create a BytesIO object to store the file content
    output = BytesIO()

    # Write header
    output.write(header_template)

    # Process each item
    for item in items:
        # Get accepted and rejected bundles
        accepted_bundles = (item.get('serial_and_batch_bundle_accepted') or '').split(',')
        rejected_bundles = (item.get('serial_and_batch_bundle_rejected') or '').split(',')
        
        # Process each accepted bundle
        for bundle_name in accepted_bundles:
            if not bundle_name.strip():
                continue
                
            # Get bundle document
            bundle_doc = frappe.get_doc('Serial and Batch Bundle', bundle_name.strip())
            
            # Process each entry in the bundle
            for index, entry in enumerate(bundle_doc.entries, 1):
                if not entry.serial_no:
                    continue
                    
                # Get serial document
                serial_doc = frappe.get_doc('Serial No', entry.serial_no.strip())
                
                # Prepare label data.
                if service_type == "Peneus Hub":
                    custom_slug = (serial_doc.custom_slug or '').upper()
                    
                    label_data = {
                        'h_line_0_1': f"CL : {(serial_doc.custom_customer or '').upper()}",
                        'h_line_0_2': f"{(serial_doc.custom_customer_code or '').upper()}",
                        'package_label': f"{(serial_doc.batch_no or '').upper()}",
                        'h_line_1_1': custom_slug[:30],  # First 30 characters
                        'h_line_1_2': '', 'h_line_1_3': '', 'h_line_1_4': '',
                        'h_line_2_1': '',
                        'h_line_2_2': custom_slug[30:60],  # Next 30 characters
                        'h_line_3_1': 'ID : ', 
                        'h_line_3_2': f"{(serial_doc.name or '').upper()}",
                        'h_line_4_1': 'COD. PR : ', 
                        'h_line_4_2': f"{(item.get('item_code') or '').upper()}",
                        'h_line_5_1': 'SKU : ', 
                        'h_line_5_2': 'NOS',
                        'h_line_6_1': 'COD. INT : ', 
                        'h_line_6_2': f"{(item.get('item_code') or '').upper()} NOS",
                        'h_line_7_1': f"{(doc.name or '').upper()}",
                        'h_line_7_2': '',
                        'barcode': (serial_doc.custom_barcode or ''),
                        'v_line_1': f"{index}/{len(bundle_doc.entries)}",
                        'vline_2': ''
                    }



                else:  # Tyre Hotel format.custom_load_index
                    label_data = {
                        
                        'customer': remove_accents((doc.customer or '')[:35]).upper(),
                        'plate': remove_accents(serial_doc.custom_license_plate or '').upper(),
                        'order_number': doc.name or '',
                        'sl_no':serial_doc.name or '',
                        'order_date': doc.creation.strftime('%d/%m/%Y') if doc.creation else '',
                        'vehicle': remove_accents(doc.mezzo or '').upper(),
                        'tyre_brand': remove_accents(serial_doc.brand or '').upper(),
                        'tyre_model': remove_accents(serial_doc.custom_model or '').upper(),
                        'tyre_size': f"{serial_doc.custom_tire_widthmm or ''}/{serial_doc.custom_aspect_ratio or ''}{serial_doc.custom_carcass or ''}{serial_doc.custom_diameterinch or ''} {serial_doc.custom_load_index or ''}{serial_doc.custom_speed_rating or ''}",
                        'season_kit_condition': f"{(doc.season or '').upper()}/{(serial_doc.custom_tyre_type or '').upper()}/{(doc.condition or '').upper()}",
                        'label_number': serial_doc.custom_barcode if serial_doc.custom_barcode else '',
                        'package_number': str(index),
                        'package_total': str(len(bundle_doc.entries))
                    }
                
                # Format the label with the data
                label_content = body_template
                for key, value in label_data.items():
                    placeholder = f"{{{key}}}"
                    if isinstance(value, str):
                        value = value.encode('utf-8')
                    else:
                        value = str(value).encode('utf-8')
                    label_content = label_content.replace(placeholder.encode('utf-8'), value)
                
                # Write the formatted label to the output
                output.write(label_content)

    # Reset the file pointer to the beginning
    output.seek(0)
    return output


def download_label_file(doc, items=None, service_type="Peneus Hub"):
   """
   Generate and download a label file
  
   Args:
       doc: Frappe document object
       items: List of items to print labels for (optional)
       service_type: Service type ('Peneus Hub' or 'Tyre Hotel')
      
   Returns:
       Response: HTTP response with file download
   """
   if items is None:
       if service_type == "Peneus Hub":
           items = doc.item_details_ph
       else:  # Tyre Hotel
           items = doc.item_details_th
  
   # Generate the label file
   output = generate_label_file(doc, items, service_type)
  
   # Prepare the file for download
   filename = f"labels_{doc.name}_{generate_random_string()}.prn"
  
   # Set up the response for file download
   frappe.response['filename'] = filename
   frappe.response['filecontent'] = output.getvalue()
   frappe.response['type'] = 'download'
   frappe.response['content_type'] = 'application/octet-stream'


# Example usage in a Frappe button method:
@frappe.whitelist()
def print_labels(doctype, docname, service_type="Peneus Hub"):
    try:
        doc = frappe.get_doc(doctype, docname)
        
        if service_type == "Peneus Hub":
            items = doc.get("item_details_ph")
        else:
            items = doc.get("item_details_th")

        if not items:
            frappe.throw(f"No items found for {service_type}")

        return download_label_file(doc, items, service_type)
    
    except Exception as e:
        frappe.log_error(title="Label Generation Error", message=frappe.get_traceback())
        frappe.respond_as_web_page(
            title="Error",
            message=f"Error generating labels: {str(e)}",
            indicator_color="red"
        )






def create_default_ph_templates(header_path, body_path):
    """Create default Peneus Hub template files"""
    ph_header = b"""##\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1eSATENH\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1eAEX0ARA3H001V001CS3#E4A103920639Z##\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1eAPSWKsenza-intesta-ty%0H0033V0025GB004001\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e&01NiceOvlZA"""
    
    ph_body = b"""%0H0120V0040P02$A,024,024,0$={h_line_0_1}
%0H0250V0040P02$A,024,024,0$={h_line_0_2}
%0H0120V0050P02$A,100,090,0$={package_label}
%0H0120V0130P02$A,024,024,0$={h_line_1_1}
%0H0250V0130P02$A,024,024,0$={h_line_1_2}
%0H0350V0130P02$A,024,024,0$={h_line_1_3}
%0H0450V0130P02$A,024,024,0$={h_line_1_4}
%0H0120V0155P02$A,024,024,0$={h_line_2_1}
%0H0250V0155P02$A,024,024,0$={h_line_2_2}
%0H0120V0180P02$A,024,024,0$={h_line_3_1}
%0H0250V0180P02$A,024,024,0$={h_line_3_2}
%0H0120V0205P02$A,024,024,0$={h_line_4_1}
%0H0250V0205P02$A,024,024,0$={h_line_4_2}
%0H0120V0230P02$A,024,024,0$={h_line_5_1}
%0H0250V0230P02$A,024,024,0$={h_line_5_2}
%0H0120V0255P02$A,024,024,0$={h_line_6_1}
%0H0250V0255P02$A,024,024,0$={h_line_6_2}
%0H0120V0280P02$A,024,024,0$={h_line_7_1}
%0H0250V0280P02$A,024,024,0$={h_line_7_2}
%0H0120V0315B102040*{barcode}*
%0H0169V0360L0101P07XM*{barcode}*
%1H0600V0300P02$A,042,030,0$={v_line_1}{vline_2}
/01
~A0
Q1Z"""
    
    with open(header_path, 'wb') as f:
        f.write(ph_header)
    
    with open(body_path, 'wb') as f:
        f.write(ph_body)

def create_default_th_templates(header_path, body_path):
    """Create default Tyre Hotel template files"""
    th_header = b"""##\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1eSATENH\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1eAEX0ARA3H001V001CS3#E4A103920639Z##\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1eAPSWKsenza-intesta-ty%0H0033V0025GB004001\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e&01NiceOvlZA"""
    
    th_body = b"""%0H0160V0030B102040*{label_number}*
%0H0100V0070P02$A,024,024,0$={customer}
%0H0100V0083P02$A,090,090,0$={plate}
%0H0100V0168P02$A,024,024,0$=ORDER:
%0H0230V0156P02$A,044,044,0$={order_number}
%0H0100V0180P02$A,024,024,0$=ID:
%0H0230V0180P02$A,044,044,0$={sl_no}
%0H0350V0180P02$A,024,024,0$=DATED
%0H0400V0180P02$A,024,024,0$={order_date}
%0H0100V0210P02$A,024,024,0$=VEHICLE:
%0H0230V0210P02$A,024,024,0$={vehicle}
%0H0100V0235P02$A,024,024,0$=BRAND:
%0H0230V0235P02$A,024,024,0$={tyre_brand}
%0H0100V0260P02$A,024,024,0$=MODEL:
%0H0230V0260P02$A,024,024,0$={tyre_model}
%0H0100V0285P02$A,024,024,0$=SIZE:
%0H0230V0285P02$A,024,024,0$={tyre_size}
%0H0100V0310P02$A,024,024,0$={season_kit_condition}
%0H0160V0340B102040*{label_number}*
%0H0209V0385L0101P07XM*{label_number}*
%1H0600V0330P02$A,042,030,0$=PACKAGE {package_number}/{package_total}
/01
~A0
Q1Z"""



    
    with open(header_path, 'wb') as f:
        f.write(th_header)
    
    with open(body_path, 'wb') as f:
        f.write(th_body)

