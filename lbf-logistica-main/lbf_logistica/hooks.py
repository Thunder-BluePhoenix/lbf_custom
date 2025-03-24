app_name = "lbf_logistica"
app_title = "LBF Logistica"
app_publisher = "Hybrowlabs"
app_description = "LBF Logistica"
app_email = "chinmay@hybrowlabs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lbf_logistica",
# 		"logo": "/assets/lbf_logistica/logo.png",
# 		"title": "LBF Logistica",
# 		"route": "/lbf_logistica",
# 		"has_permission": "lbf_logistica.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lbf_logistica/css/lbf_logistica.css"
# app_include_js = "/assets/lbf_logistica/js/lbf_logistica.js"


# include js, css files in header of web template
# web_include_css = "/assets/lbf_logistica/css/lbf_logistica.css"
# web_include_js = "/assets/lbf_logistica/js/lbf_logistica.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lbf_logistica/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}



# include js in doctype views
doctype_js = {
                "Quality Inspection" : "public/js/quality_inspection.js",
                "Item": "public/js/item.js",
                "Material Request": "public/js/material_request.js",
                "Stock Entry": "public/js/stock_entry.js",
                "Pick List":"public/js/pick_list.js",
                "Sales Invoice":"public/js/invoice.js",
                "Driver":"public/js/driver.js",
                "Pricing Rule":"public/js/pricing_rule.js",
                "Address": "public/js/address.js"

            }
doctype_list_js = {"Pick List" : "public/js/pick_list_listview.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lbf_logistica/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]



fixtures = [
    {"dt": "Item", "filters": [["name", "in", ["Other"]]]},
    {"dt": "Warehouse", "filters": [["name", "in", ["Special Customer Warehouse - LL"]]]},
    
    # {"dt": "Dashboard", "filters": [["name", "in", ["Team Tasks Overview"]]]},
    # {"dt": "Dashboard Chart", "filters": [["name", "in", ["Tasks per Team", "Task Status Distribution"]]]}
]
# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lbf_logistica.utils.jinja_methods",
# 	"filters": "lbf_logistica.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lbf_logistica.install.before_install"
# after_install = "lbf_logistica.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lbf_logistica.uninstall.before_uninstall"
# after_uninstall = "lbf_logistica.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lbf_logistica.utils.before_app_install"
# after_app_install = "lbf_logistica.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lbf_logistica.utils.before_app_uninstall"
# after_app_uninstall = "lbf_logistica.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lbf_logistica.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
                "Item":{
                    "before_save":["lbf_logistica.overrides.item.before_save_item",
                                    "lbf_logistica.overrides.item.add_titolo" ]
                },

                "Quality Inspection": {
                    "on_submit": "lbf_logistica.overrides.quality_inspection.update_quality_inspection_done"
                },
                "Pricing Rule": {
                    "before_save": "lbf_logistica.overrides.pricing_rule.update_bill_of_landing_charges",
                },
                "Serial No": {"before_save":"lbf_logistica.overrides.serialno_barcode.before_save_serial"},
                "Supplier": {"before_save":"lbf_logistica.overrides.supplier_address.update_address_and_contact",
                             "on_update":"lbf_logistica.overrides.supplier_address.update_supplier_in_customer"},

                "Address":{"before_save":"lbf_logistica.overrides.customer.validate_default_supplier_address"},

                # "Stock Entry": {"validate": "lbf_logistica.overrides.stock_entry_scan_barcode.validate"}validate_submit.validate_default_supplier
            

                "Material Request Instruction Log" :{
                    # "before_submit": "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.check_time_before_submit",
                    "on_submit": "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.create_material_request",
                },
                "Material Request":{"before_save":["lbf_logistica.overrides.material_request.purpose_selection",
                                                   "lbf_logistica.overrides.material_request.update_req_qty"],
                                    "on_submit":[
                                                 "lbf_logistica.overrides.material_request.create_serial_and_batch",
                                                 "lbf_logistica.overrides.material_request.update_mr_ins_log",
                                                 "lbf_logistica.overrides.material_request.create_bill_of_lading_and_shipment",
                                                 "lbf_logistica.overrides.material_request.create_pick_listfrom_hooks",],
                                    "before_submit": [
                                                        "lbf_logistica.overrides.material_request.validate_submit"
                                                    ],
                                    

                                    },
                "Pick List": {
                        "before_save" : ["lbf_logistica.overrides.pick_list.before_save_loc_val",
                                         "lbf_logistica.overrides.pick_list.validate_total_selected_qty"],
                        
                        # "after_save": "lbf_logistica.overrides.pick_list.force_submit_pick_list",validate_submit

                        "before_submit": [
                            "lbf_logistica.overrides.pick_list.populate_item_locations",
                            "lbf_logistica.overrides.pick_list.validate_submit"
                        ],
                        "on_submit": [
                            "lbf_logistica.overrides.pick_list.status_change_on_submit"
                        ],
                        "on_cancel": "lbf_logistica.overrides.pick_list.status_change_on_cancel",
                        "on_update":"lbf_logistica.overrides.pick_list.populate_item_locations_json"
                    },
                "Sales Invoice":{"before_save": ["lbf_logistica.overrides.invoice.check_and_validate_pricingrule",
                                                 "lbf_logistica.overrides.invoice.validate_dates"],
                                 "on_submit": "lbf_logistica.overrides.invoice.on_submit_total",
                                 "on_cancel": "lbf_logistica.overrides.invoice.status_change_on_cancel"},
                "Delivery Trip":{"on_submit": "lbf_logistica.overrides.delivery_trip.update_shipment_from_delivery_trip",
                                "on_update_after_submit":"lbf_logistica.overrides.delivery_trip.update_shipment_status_from_delivery_trip"},

                "Stock Entry": {"on_submit": "lbf_logistica.overrides.stock_entry.update_serial_nos",
                                "before_submit": "lbf_logistica.overrides.stock_entry.validate_onsubmit"}
                          

# override_doctype_class = {
#     "Pick List": "lbf_logistica.overrides.custom_document.CustomDocument"
# }

}

override_doctype_class = {
    "Pricing Rule": "lbf_logistica.overrides.pricing_rule.CustomPricingRule",
    "Sales Invoice": "lbf_logistica.overrides.invoice.CustomSalesInvoice",
    "Pick List": ["lbf_logistica.overrides.pick_list.CustomPickList",
                  "lbf_logistica.overrides.pick_list.CustomDocument"
    ],
    "Stock Entry":"lbf_logistica.overrides.stock_entry.CustomStockEntry"

}


app_include_routes = [
    {"methods": ["POST"], "path": "/api/method/lbf_logistica.api.bol.save_material_request_instruction_log", "handler": "lbf_logistica.api.bol.save_material_request_instruction_log"},
]


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lbf_logistica.tasks.all"
# 	],
# 	"daily": [
# 		"lbf_logistica.tasks.daily"
# 	],
# 	"hourly": [
# 		"lbf_logistica.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lbf_logistica.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lbf_logistica.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lbf_logistica.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lbf_logistica.event.get_events"
# }
override_whitelisted_methods = {
    "frappe.desk.treeview.get_children": "lbf_logistica.overrides.customer.get_children"
}

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lbf_logistica.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lbf_logistica.utils.before_request"]
# after_request = ["lbf_logistica.utils.after_request"]

# Job Events
# ----------
# before_job = ["lbf_logistica.utils.before_job"]
# after_job = ["lbf_logistica.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lbf_logistica.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

