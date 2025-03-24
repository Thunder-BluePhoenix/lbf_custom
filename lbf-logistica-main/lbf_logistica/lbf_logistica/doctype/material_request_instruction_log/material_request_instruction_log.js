// Copyright (c) 2024, Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Request Instruction Log', {
    onload: function (frm) {
        // Filter for 'items' table
        frm.fields_dict["items"].grid.get_field("item_code").get_query = function (doc, cdt, cdn) {
            if (frm.doc.material_request_type === "Redelivery") {
                if (!frm.doc.customer) {
                    return {};
                }

                return {
                    filters: {
                        name: ["in", (function () {
                            let item_codes = [];
                            frappe.call({
                                method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_item_codes_for_customer",
                                args: {
                                    customer: frm.doc.customer
                                },
                                async: false,
                                callback: function (response) {
                                    if (response.message) {
                                        item_codes = response.message;
                                    }
                                }
                            });
                            return item_codes;
                        })()]
                    }
                };
            } else if (frm.doc.material_request_type === "Pick Up") {
                return {
                    query: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_items_with_others",
                    filters: {
                        customer: frm.doc.customer
                    }
                };
            } else {
                return {};
            }
        };

        // Filter for 'th_items' table
        frm.fields_dict["th_items"].grid.get_field("item_code").get_query = function (doc, cdt, cdn) {
            if (frm.doc.material_request_type === "Redelivery") {
                if (!frm.doc.customer) {
                    return {};
                }

                return {
                    query: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.search_th_items_for_link_field",
                    filters: {
                        customer: frm.doc.customer,
                        license_plate: frm.doc.license_plate || null
                    }
                };
        
        
            } else if (frm.doc.material_request_type === "Pick Up") {
                return {
                    query: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_items_with_others",
                    filters: {
                        customer: frm.doc.customer
                    }
                };
            } else {
                return {};
            }
        };
    },
    party_type: function(frm) {
        customer_party_type_filter(frm);
        
    },
    shipping_address_name: function(frm) {
        transporter_filter(frm);
        if (frm.doc.shipping_address_name) {
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'Address', name: frm.doc.shipping_address_name},
                callback: function(response) {
                    if (response.message) {
                        let address = response.message;
                        frm.set_value('address', `${address.address_title || ''} · ${address.address_type || ''}
${address.address_line1 || ''}
${address.city || ''}, ${address.state || ''}
PIN Code: ${address.pincode || ''}
${address.country || ''}
                        `);
                    }
                }
            });
        } else {
            frm.set_value('address', '');
        }
    },
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.fetch_customer_address",
                args: {
                    customer: frm.doc.customer
                },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('address_of_customer', response.message);
                    } else {
                        frm.set_value('address_of_customer', 'No address found');
                    }
                }
            });
        } else {
            frm.set_value('address_of_customer', '');
        }
        shipping_to_filter(frm);
    },
    transporter_name: function(frm) {
        if (frm.doc.transporter_name) {
            frappe.call({
                method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.fetch_supplier_address",
                args: {
                    supplier: frm.doc.transporter_name
                },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('transporter_address', response.message);
                    } else {
                        frm.set_value('transporter_address', 'No address found');
                    }
                }
            });
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Supplier',
                    name: frm.doc.transporter_name
                },
                callback: function(response) {
                    if(response.message && response.message.custom_weekdays_off) {
                        // Clear existing rows
                        frm.clear_table('weekdays_off');
                        
                        // Add each weekday from supplier's custom_weekdays_off to instruction log's weekdays_off
                        response.message.custom_weekdays_off.forEach(function(weekday) {
                            let row = frm.add_child('weekdays_off');
                            // Copy all fields from the source row to the target row
                            Object.keys(weekday).forEach(function(key) {
                                row[key] = weekday[key];
                            });
                        });
                        
                        frm.refresh_field('weekdays_off');
                    }
                }
            });
        } else {
            frm.set_value('transporter_address', '');
            frm.clear_table('weekdays_off');
            frm.refresh_field('weekdays_off');
        }
    },
    customer_contact: function(frm) {
        if (frm.doc.customer_contact) {
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'Contact', name: frm.doc.customer_contact },
                callback: function(response) {
                    if (response.message) {
                        let contact = response.message;
                        let primary_phone = (contact.phone_nos || []).find(phone => phone.is_primary_phone);
                        frm.set_value('contact_person', contact.first_name || 'No name available');
                        frm.set_value('contact', primary_phone ? primary_phone.phone : 'No primary phone available');
                        frm.set_value('email', contact.email_id || 'No primary email available');
                    }
                }
            });
        } else {
            frm.set_value('contact_person', '');
            frm.set_value('contact', '');
            frm.set_value('email', '');
        }
    },
    service: function(frm) {
        
        if (frm.doc.service === "Peneus Hub") {
           
            frm.set_df_property('material_request_type', 'options', '\nRedelivery');
        } 
        // else if (frm.doc.custom_service === "Tyre Hotel") {
        //     frm.set_df_property('custom_p_purpose', 'options', '\nPick Up');
        // }
         else {
            frm.set_df_property('material_request_type', 'options', '\nRedelivery\nPick Up');
        }
        
        if (frm.doc.service === "Tyre Hotel") {
            
            // Make 'items' table not mandatory
            frm.set_df_property('items', 'reqd', 0);
        } else {
            // Restore mandatory when 'service' is not 'Tyre Hotel'
            frm.set_df_property('items', 'reqd', 1);
        }
        
    },
    refresh: function (frm) {
        shipping_to_filter(frm);
        customer_party_type_filter(frm);
        // transporter_filter(frm);
    },

   
    shipping_to: function (frm) {

        if (frm.doc.shipping_to) {
            // Filter Address based on selected Shipment (Customer)
            frm.set_query('shipping_address_name', function () {
                return {
                    filters: {
                        link_doctype: 'Customer',
                        link_name: frm.doc.shipping_to
                    }
                };
            });

            // Filter Contact based on selected Shipment (Customer)
            frm.set_query('customer_contact', function () {
                return {
                    filters: {
                        link_doctype: 'Customer',
                        link_name: frm.doc.shipping_to
                    }
                };
            });

            // Fetch and set the first Address and Contact by default
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Address',
                    fields: ['name'],
                    filters: [
                        ['Dynamic Link', 'link_doctype', '=', 'Customer'],
                        ['Dynamic Link', 'link_name', '=', frm.doc.shipping_to]
                    ],
                    // order_by: 'tabAddress.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('shipping_address_name', response.message[0].name);
                    } else {
                        frm.set_value('shipping_address_name', null);
                    }
                }
            });

            // Fetch and set the first Contact by default
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Contact',
                    fields: ['name'],
                    filters: [
                        ['Dynamic Link', 'link_doctype', '=', 'Customer'],
                        ['Dynamic Link', 'link_name', '=', frm.doc.shipping_to]
                    ],
                    // order_by: 'tabContact.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('customer_contact', response.message[0].name);
                    } else {
                        frm.set_value('customer_contact', null);
                    }
                }
            });
        } else {
            // Clear Address and Contact if Shipment is cleared
            frm.set_value('shipping_address_name', null);
            frm.set_value('customer_contact', null);
        }
    },
});




// frappe.ui.form.on('Material Request Instruction Log', {
//     contact_person: function(frm) {
//         if (frm.doc.contact_person) {
//             frappe.call({
//                 method: 'frappe.client.get',
//                 args: {
//                     doctype: 'Contact',
//                     name: frm.doc.contact_person
//                 },
//                 callback: function(response) {
//                     if (response.message) {
//                         let contact = response.message;
//                         frm.set_value('contact', contact.phone || '');
//                     }
//                 }
//             });
//         } else {
//             frm.set_value('contact', '');
//         }
//     }
// });


frappe.ui.form.on('Material Request Item', {
    qty: function(frm, cdt, cdn) {
        if (frm.doc.material_request_type === "Redelivery" && frm.doc.service === "Peneus Hub") { 
            let row = frappe.get_doc(cdt, cdn);
            if (row.item_code && frm.doc.customer) {
                let total_qty_for_item = 0;

                frm.doc.items.forEach(item => {
                    if (item.item_code === row.item_code) {
                        total_qty_for_item += item.qty || 0;
                    }
                });

                // Call the server-side method to get the actual stock
                frappe.call({
                    method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_total_actual_qty",
                    args: {
                        item_code: row.item_code,
                        customer: frm.doc.customer  // Pass the customer as an argument
                    },
                    callback: function(response) {
                        let total_actual_qty = response.message || 0;

                        // Check if the total requested qty exceeds the available stock
                        if (total_qty_for_item > total_actual_qty) {
                            frappe.msgprint(__('The total quantity ({0}) entered for item {1} exceeds available stock ({2}) for customer {3}.', 
                                [total_qty_for_item, row.item_code, total_actual_qty, frm.doc.customer]));
                        }
                    }
                });
            }
        }
    },
    item_code: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.item_code && frm.doc.customer && frm.doc.material_request_type === "Redelivery" && frm.doc.service === "Peneus Hub") {
            frappe.call({
                method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_total_actual_qty",
                args: {
                    item_code: row.item_code,
                    customer: frm.doc.customer
                },
                callback: function(response) {
                    let actual_qty = response.message || 0;
                    frappe.model.set_value(cdt, cdn, 'custom_max_order_qty', actual_qty);
                    frm.refresh_field('items');
                }
            });
        }
    }

});

frappe.ui.form.on('MR Instruction Log Item TH', {
    qty: function(frm, cdt, cdn) {
        if (frm.doc.material_request_type === "Redelivery" && frm.doc.service === "Tyre Hotel") { 
            let row = frappe.get_doc(cdt, cdn);
            if (row.item_code && frm.doc.customer) {
                let total_qty_for_item = 0;

                frm.doc.th_items.forEach(item => {
                    if (item.item_code === row.item_code && item.type === row.type) {
                        total_qty_for_item += item.qty || 0;
                    }
                });

                // Call the server-side method to get the actual stock
                frappe.call({
                    method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_total_actual_qty_for_th",
                    args: {
                        item_code: row.item_code,
                        customer: frm.doc.customer,
                        tyre_type: row.type,
                        license_plate: frm.doc.license_plate || null
                    },
                    callback: function(response) {
                        let total_actual_qty = response.message || 0;

                        // Check if the total requested qty exceeds the available stock
                        if (total_qty_for_item > total_actual_qty) {
                            frappe.msgprint(__('The total quantity ({0}) entered for item {1} exceeds available stock ({2}) for customer {3}.', 
                                [total_qty_for_item, row.item_code, total_actual_qty, frm.doc.customer]));
                        }
                    }
                });
            }
        }
    },
    item_code: function(frm, cdt, cdn) {
        update_max_order_qty(frm, cdt, cdn);
    },

    type: function(frm, cdt, cdn) {
        update_max_order_qty(frm, cdt, cdn);
    }


});

function update_max_order_qty(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    
    if (!row.item_code || !row.type || !frm.doc.customer) {
        console.warn("Missing required fields:", { item_code: row.item_code, tyre_type: row.type, customer: frm.doc.customer });
        return;
    }
    
    if (frm.doc.material_request_type === "Redelivery" && frm.doc.service === "Tyre Hotel") {
        console.log("Fetching max_order_qty for:", row.item_code, row.type, frm.doc.customer);

        frappe.call({
            method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_total_actual_qty_for_th",
            args: {
                item_code: row.item_code,
                customer: frm.doc.customer,
                tyre_type: row.type, // Pass tyre_type
                license_plate: frm.doc.license_plate || null
            },
            callback: function(response) {
                console.log("Response received:", response);
                let actual_qty = response.message || 0;
                frappe.model.set_value(cdt, cdn, 'max_order_qty', actual_qty);
                frappe.model.set_value(cdt, cdn, 'qty', actual_qty);
            },
            error: function(err) {
                console.error("Error fetching max_order_qty:", err);
            }
        });
    }
}

function shipping_to_filter(frm){
    if (frm.doc.customer) {
        frappe.call({
            method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_child_customers",  
            args: { customer_name: frm.doc.customer },
            callback: function (r) {
                if (r.message) {
                    let customers = r.message;

                    frm.set_query('shipping_to', function () {
                        return {
                            filters: { name: ['in', customers] }
                        };
                    });
                } else {
                    console.log("No child customers found.");
                }
            }
        });
    } else {
        frm.set_query('shipping_to', function () {
            return {};
        });
    }

}

function customer_party_type_filter(frm){
    if (frm.doc.party_type) {
        frm.set_query('customer', function() {
            return {
                filters: {
                    customer_group: frm.doc.party_type
                }
            };
        });
    } else {
        frm.set_query('customer', function() {
            return {}; 
        });
    }
}

function transporter_filter(frm){
    if (frm.doc.shipping_address_name) {
        frappe.db.get_doc('Address', frm.doc.shipping_address_name).then((customer) => {
            console.log(customer);
            if (customer && customer.custom_transporters) {
                console.log(customer, customer.custom_transporters);

                // Filter suppliers where is_transporter is checked
                const transporter_suppliers = customer.custom_transporters
                    .filter(row => row.is_transporter)
                    .map(row => row.supplier);
                
                console.log(transporter_suppliers);

                // Find the default supplier with is_transporter checked
                const default_transporter = customer.custom_transporters.find(row => row.is_transporter && row.is_default);

                // Set query for transporter_name field
                frm.set_query('transporter_name', function () {
                    return {
                        filters: {
                            name: ['in', transporter_suppliers]
                        }
                    };
                });

                // Set default value for transporter_name
                if (default_transporter) {
                    frm.set_value('transporter_name', default_transporter.supplier);
                } else if (transporter_suppliers.length > 0) {
                    frm.set_value('transporter_name', transporter_suppliers[0]);
                } else {
                    frm.set_value('transporter_name', null);
                }
            }
        });
    } else {
        // Clear transporter field and reset query
        frm.set_query('transporter_name', function () {
            return {};
        });

        frm.set_value('transporter_name', null);
    }
}

// frappe.ui.form.on('Material Request Instruction Log', {
//     onload: function(frm) {
//         frm.set_query('shipping_address_name', function() {
//             if (!frm.doc.shipping_to) {
//                 return {}; 
//             }
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.shipping_to}
//             };
//         });
//          // Filter for custom_customer_contact
//          frm.set_query('customer_contact', function() {
//             if (!frm.doc.shipping_to) {
//                 return {};
//             }
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.shipping_to}
//             };
//         });
//     }
// });
















// frappe.ui.form.on('MR Instruction Log Item TH', {
//     item_code: function(frm, cdt, cdn) {
//         const row = locals[cdt][cdn];
//         if (row.item_code && frm.doc.material_request_type === "Redelivery") {
//             frappe.call({
//                 method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_th_item_codes_for_customer",
//                 args: {
//                     customer: frm.doc.customer,
//                     license_plate: frm.doc.license_plate || null
//                 },
//                 callback: function(response) {
//                     if (response.message) {
//                         const items = response.message;
//                         const selected_item = items.find(item => item.item_code === row.item_code);
//                         if (selected_item) {
//                             frappe.model.set_value(cdt, cdn, 'type', selected_item.custom_tyre_type);
//                         }
//                     }
//                 }
//             });
//         }
//     }
// });







frappe.provide("frappe.item_tyre_type_map");

// Event handler to populate the tyre type field
frappe.ui.form.on('MR Instruction Log Item TH', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.item_code && frm.doc.material_request_type === "Redelivery" && frm.doc.customer) {
            // Get the currently selected item's dropdown description to extract tyre type
            const $dropdown = $(`.frappe-control[data-fieldname="item_code"]`).last();
            const selected_text = $dropdown.find('.control-value').text();
            
            // Extract tyre type from the description if possible
            const match = selected_text.match(/Type:\s*(.+)$/);
            if (match && match[1]) {
                frappe.model.set_value(cdt, cdn, 'type', match[1].trim());
            } else {
                // Fallback to server call if we can't get it from the UI
                frappe.call({
                    method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_item_tyre_type",
                    args: {
                        customer: frm.doc.customer,
                        item_code: row.item_code,
                        license_plate: frm.doc.license_plate || null
                    },
                    callback: function(response) {
                        if (response.message) {
                            frappe.model.set_value(cdt, cdn, 'type', response.message);
                        }
                    }
                });
            }
        }
    }
});

