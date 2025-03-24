import json
from os import path


import frappe




# def create_or_update(json_file_path):
#    json_file = open(json_file_path, "r")
#    json_data = json.load(json_file)
#    json_file.close()


#    doc_name = json_data["name"]
#    doc_doctype = json_data["doctype"]
#    del json_data["modified"]


#    # check if already exists in database
#    exists = frappe.db.exists(doc_doctype, doc_name)


#    doc = (
#        frappe.get_doc(doc_doctype, doc_name) if exists else frappe.new_doc(doc_doctype)
#    )
#    doc.update(json_data)
#    doc.save()




# def execute():
#    json_file_path = path.join(
#        path.dirname(__file__), "files", "lead_call_validations.json"
#    )
#    create_or_update(json_file_path)



funnel_json_files=["ph_notifications.json", "th_notifications.json", "mr_submission.json"]
data=[]
for json_file in funnel_json_files:
    json_file_path = path.join(
        path.dirname(__file__), "files", json_file
    )
    json_file = open(json_file_path, "r")
    json_data = json.load(json_file)
    json_file.close()
    data.append(json_data)

def execute():
    for d in data:
        if not frappe.db.exists("Funnel", d.get("name")):
            frappe.get_doc(d).insert(ignore_permissions=True)
        else:
            funnel_doc = frappe.get_doc("Funnel", d.get("name"))
            defination_jsons=d.get("funnel_definition")
            d.pop("funnel_definition")
            funnel_doc.update(d)
            funnel_doc.funnel_definition=[]
            for defination_json in defination_jsons:
                defination_json.pop("name")
                def_doc = frappe.new_doc("Funnel Definition")
                def_doc.update(defination_json)
                funnel_doc.funnel_definition.append(def_doc)
            funnel_doc.flags.ignore_version = True
            funnel_doc.save()

