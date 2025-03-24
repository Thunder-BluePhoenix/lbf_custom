// Copyright (c) 2024, Hybrowlabs and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Wise Item Balance"] = {
	"filters" : [
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 1
		}
	]
};
