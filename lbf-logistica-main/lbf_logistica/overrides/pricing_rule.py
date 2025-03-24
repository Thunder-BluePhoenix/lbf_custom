import frappe
from frappe.utils import flt
from erpnext.accounts.doctype.pricing_rule.pricing_rule import PricingRule

def update_bill_of_landing_charges(doc, method):
    bill_of_landings = frappe.get_all(
        "Bill Of Landing",
        filters={"customer": doc.custom_customerr, "docstatus": ["=", 0]},
        fields=["name"]
    )
    
    for bill in bill_of_landings:
        bill_doc = frappe.get_doc("Bill Of Landing", bill.name)

        for item in bill_doc.item_details_ph:
            item_matches_rule = False

            # Process based on the `apply_on` field
            if doc.apply_on == "Item Code":
                item_matches_rule = any(row.item_code == item.item_code for row in doc.items)

            elif doc.apply_on == "Item Group":
                item_group = frappe.db.get_value("Item", item.item_code, "item_group")
                item_matches_rule = any(row.item_group == item_group for row in doc.item_groups)

            elif doc.apply_on == "Brand":
                item_brand = frappe.db.get_value("Item", item.item_code, "brand")
                item_matches_rule = any(row.brand == item_brand for row in doc.brands)
            
            # elif doc.apply_on == "Transaction":
            #     item_matches_rule = True 

            # If the item matches the Pricing Rule, process Handling In and Out Charges
            if item_matches_rule:
                # Handling IN Charges
                if doc.custom_handling_in:
                    exists_in = any(
                        row.item_code == item.item_code for row in bill_doc.handling_in_charges
                    )
                    if not exists_in:
                        bill_doc.append("handling_in_charges", {
                            "item_name": item.item_name,
                            "item_code": item.item_code,
                            "rate": flt(doc.custom_amount_handling_in),
                            "accepted_qty": flt(item.accepted_qty),
                            "amount": flt(doc.custom_amount_handling_in) * flt(item.accepted_qty)
                        })
                        frappe.msgprint(f"Added Handling In Charge for Item: {item.item_code} in Bill Of Landing: {bill_doc.name}.")
                    else:
                        frappe.msgprint(f"Handling In Charge already exists for Item: {item.item_code} in Bill Of Landing: {bill_doc.name}.")

                # Handling OUT Charges
                if doc.custom_handling_out:
                    exists_out = any(
                        row.item_code == item.item_code for row in bill_doc.handling_out_charges
                    )
                    if not exists_out:
                        bill_doc.append("handling_out_charges", {
                            "item_name": item.item_name,
                            "item_code": item.item_code,
                            "rate": flt(doc.custom_amount_handling_out),
                            "accepted_qty": flt(item.accepted_qty),
                            "amount": flt(doc.custom_amount_handling_out) * flt(item.accepted_qty)
                        })
                        frappe.msgprint(f"Added Handling Out Charge for Item: {item.item_code} in Bill Of Landing: {bill_doc.name}.")
                    else:
                        frappe.msgprint(f"Handling Out Charge already exists for Item: {item.item_code} in Bill Of Landing: {bill_doc.name}.")

        # Save the updated Bill Of Landing
        bill_doc.flags.ignore_validate_update_after_submit = True
        bill_doc.save(ignore_permissions=True)





class CustomPricingRule(PricingRule):
    def validate_applicable_for_selling_or_buying(self):
        # Override to bypass the validation
        pass
