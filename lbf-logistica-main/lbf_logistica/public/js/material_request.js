frappe.ui.form.on('Material Request', {
    refresh: function (frm) {
        setTimeout(function () {
            frm.remove_custom_button('Stop');
            frm.remove_custom_button('Pick List', 'Create');
            frm.remove_custom_button('Material Transfer', 'Create');
            frm.remove_custom_button('Material Transfer (In Transit)', 'Create');
            frm.remove_custom_button('Sales Order', 'Get Items From');
            frm.remove_custom_button('Bill of Materials', 'Get Items From');
            frm.remove_custom_button('Product Bundle', 'Get Items From');
            // if (frm.doc.custom_p_purpose === 'Redelivery' && frm.doc.docstatus === 1) {
            //     frm.add_custom_button(__('Create Pick List'), () => {
            //         frappe.call({
            //             method: "lbf_logistica.overrides.material_request.create_pick_list",
            //             args: {
            //                 doc_name: frm.doc.name
            //             },
            //             callback: function (response) {
            //                 console.log(response, "response");
            //                 if (response.message && response.message.length > 0) {
            //                     response.message.forEach(pickListData => {
            //                         frappe.call({
            //                             method: "frappe.client.insert",
            //                             args: {
            //                                 doc: pickListData
            //                             },
            //                             callback: function (res) {
            //                                 if (res.message) {
                                             
            //                                     frappe.call({
            //                                         method: "frappe.client.submit",
            //                                         args: {
            //                                             doc: res.message
            //                                         },
            //                                         callback: function (submit_res) {
            //                                             if (submit_res.message) {
            //                                                 frappe.msgprint({
            //                                                     title: __('Pick List Submitted'),
            //                                                     indicator: 'green',
            //                                                     message: `Pick List ${submit_res.message.name} has been successfully created and submitted.`
            //                                                 });
            //                                             }
            //                                         }
            //                                     });
            //                                 }
            //                             }
            //                         });
            //                     });
            //                 } else {
            //                     frappe.msgprint({
            //                         title: __('Error'),
            //                         indicator: 'red',
            //                         message: __('Could not create Pick Lists. Please check the logs.')
            //                     });
            //                 }
            //             }
            //         });
            //     }, __("Create"));
            // }
        }, 300);
        customer_party_type_filter(frm);
        shipping_to_filter(frm);
    },
    onload: function (frm) {
   
        frm.set_df_property('material_request_type', 'options', ['Redelivery', 'Pick Up']);
    },
    custom_shipping_address_name: function(frm) {
        transporter_filter(frm);
        if (frm.doc.custom_shipping_address_name) {
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'Address', name: frm.doc.custom_shipping_address_name },
                callback: function(response) {
                    if (response.message) {
                        let address = response.message;
                        frm.set_value('custom_address', `${address.address_title || ''} · ${address.address_type || ''}
${address.address_line1 || ''}
${address.city || ''}, ${address.state || ''}
PIN Code: ${address.pincode || ''}
${address.country || ''}
                        `);
                    }
                }
            });
        } else {
            frm.set_value('custom_address', '');
        }
    },
    custom_party_type: function(frm) {
        customer_party_type_filter(frm);
    },
    custom_customer_: function(frm) {
        shipping_to_filter(frm);
        if (frm.doc.custom_customer_) {
            frappe.call({
                method: "lbf_logistica.overrides.material_request.fetch_customer_address",
                args: {
                    customer: frm.doc.custom_customer_
                },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('custom_address_of_customer', response.message);
                    } else {
                        frm.set_value('custom_address_of_customer', 'No address found');
                    }
                }
            });
        } else {
            frm.set_value('custom_address_of_customer', '');
        }
    },
    
    custom_service: function(frm) {
        if (frm.doc.custom_service === "Peneus Hub") {
            frm.set_df_property('custom_p_purpose', 'options', '\nRedelivery');
        } 
        // else if (frm.doc.custom_service === "Tyre Hotel") {
        //     frm.set_df_property('custom_p_purpose', 'options', '\nPick Up');
        // }
         else {
            frm.set_df_property('custom_p_purpose', 'options', '\nRedelivery\nPick Up');
        }
    },
    custom_customer_contact: function(frm) {
        if (frm.doc.custom_customer_contact) {
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'Contact', name: frm.doc.custom_customer_contact },
                callback: function(response) {
                    if (response.message) {
                        let contact = response.message;
                        let primary_phone = (contact.phone_nos || []).find(phone => phone.is_primary_phone);
                        frm.set_value('custom_contact_person', contact.first_name || 'No name available');
                        frm.set_value('custom_contact', primary_phone ? primary_phone.phone : 'No primary phone available');
                    }
                }
            });
        } else {
            frm.set_value('custom_contact_person', '');
            frm.set_value('custom_contact', '');
        }
    },
    custom_transporter_name: function(frm) {
        if (frm.doc.custom_transporter_name) {
            frappe.call({
                method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.fetch_supplier_address",
                args: {
                    supplier: frm.doc.custom_transporter_name
                },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('custom_transporter_address', response.message);
                    } else {
                        frm.set_value('custom_transporter_address', 'No address found');
                    }
                }
            });
        } else {
            frm.set_value('custom_transporter_address', '');
        }
    },
    custom_create_other_item_and_submit_mr: function (frm) {
        let child_table = frm.doc.custom_th_items || [];
        let promises = [];
        let has_other_items = false;

        child_table.forEach(row => {
            if (row.item_code === "Others" || row.item_code === "Other") {
                has_other_items = true;
                promises.push(
                    frappe.call({
                        method: 'lbf_logistica.overrides.material_request.create_item_from_material_request',
                        args: {
                            row_data: JSON.stringify(row)
                        }
                    }).then(r => {
                        if (r.message) {
                            frappe.model.set_value(row.doctype, row.name, 'item_code', r.message);
                            frappe.msgprint(__('Item Created with Item Code: ' + r.message));
                        }
                    })
                );
            }
        });

        if (has_other_items) {
            Promise.all(promises).then(() => {
                frm.save().then(() => { 
                    frappe.msgprint(__('All "Other" items have been created and updated in the child table.'));
                    frm.save('Submit');
        


                    
                });
            }).catch(error => {
                console.error(error);
                frappe.msgprint(__('An error occurred while processing "Other" items.'));
            });
        } else {
            frappe.msgprint(__('No "Other" items found in the child table.'));
        }
    },
    custom_shipping_to: function (frm) {
        if (frm.doc.custom_shipping_to) {
            // Filter Address based on selected Shipment (Customer)
            frm.set_query('custom_shipping_address_name', function () {
                return {
                    filters: {
                        link_doctype: 'Customer',
                        link_name: frm.doc.custom_shipping_to
                    }
                };
            });

            // Filter Contact based on selected Shipment (Customer)
            frm.set_query('custom_customer_contact', function () {
                return {
                    filters: {
                        link_doctype: 'Customer',
                        link_name: frm.doc.custom_shipping_to
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
                        ['Dynamic Link', 'link_name', '=', frm.doc.custom_shipping_to]
                    ],
                    // order_by: 'tabAddress.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('custom_shipping_address_name', response.message[0].name);
                    } else {
                        frm.set_value('custom_shipping_address_name', null);
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
                        ['Dynamic Link', 'link_name', '=', frm.doc.custom_shipping_to]
                    ],
                    // order_by: 'tabContact.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('custom_customer_contact', response.message[0].name);
                    } else {
                        frm.set_value('custom_customer_contact', null);
                    }
                }
            });
        } else {
            // Clear Address and Contact if Shipment is cleared
            frm.set_value('custom_shipping_address_name', null);
            frm.set_value('custom_customer_contact', null);
        }
    }


});


// frappe.ui.form.on('Material Request', {
//     refresh: function (frm) {
//         setTimeout(function() {
//             // if (frm.doc.docstatus === 1) {  // Check if the Sales Order is submitted
//                 // Hide the buttons by their labels
//                 frm.remove_custom_button('Stop');
//                 frm.remove_custom_button('Pick List', 'Create');
//                 frm.remove_custom_button('Material Transfer', 'Create');
//                 frm.remove_custom_button('Material Transfer (In Transit)', 'Create');
//                 frm.remove_custom_button('Sales Order', 'Get Items From');
//                 frm.remove_custom_button('Bill of Materials', 'Get Items From');
//                 frm.remove_custom_button('Product Bundle', 'Get Items From');
                
        
//                 if (frm.doc.custom_p_purpose === 'Redelivery' && frm.doc.docstatus === 1) {
//                     frm.add_custom_button(__('Create Pick List'), () => {
//                         frappe.call({
//                             method: "lbf_logistica.overrides.material_request.create_pick_list",
//                             args: {
//                                 doc_name: frm.doc.name
//                             },
//                             callback: function (response) {
//                                 console.log(response,"response");
//                                 if (response.message && response.message.length > 0) {
//                                     let links = response.message.map(pl =>
//                                         `<a href="/app/pick-list/${pl}" target="_blank">${pl}</a>`
//                                     ).join('<br>');
//                                     frappe.msgprint({
//                                         title: __('Pick Lists Created'),
//                                         indicator: 'green',
//                                         message: `The following Pick Lists were created:<br>${links}`
//                                     });
//                                 } else {
//                                     frappe.msgprint({
//                                         title: __('Error'),
//                                         indicator: 'red',
//                                         message: __('Could not create Pick Lists. Please check the logs.')
//                                     });
//                                 }
//                             }
//                         });
//                     }, __("Create"));
//                 }
//             }, 300); 
//     }
//  });





function customer_party_type_filter(frm){
    if (frm.doc.custom_party_type) {
        frm.set_query('custom_customer_', function() {
            return {
                filters: {
                    customer_group: frm.doc.custom_party_type
                }
            };
        });
    }
}

function shipping_to_filter(frm){
    if (frm.doc.custom_customer_) {
        frappe.call({
            method: "lbf_logistica.lbf_logistica.doctype.material_request_instruction_log.material_request_instruction_log.get_child_customers",  
            args: { customer_name: frm.doc.custom_customer_ },
            callback: function (r) {
                if (r.message) {
                    let customers = r.message;

                    frm.set_query('custom_shipping_to', function () {
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
        frm.set_query('custom_shipping_to', function () {
            return {};
        });
    }

}

function transporter_filter(frm){
    if (frm.doc.custom_shipping_address_name) {
        frappe.db.get_doc('Address', frm.doc.custom_shipping_address_name).then((customer) => {
            if (customer && customer.custom_transporters) {
                console.log(customer, customer.custom_transporters);

                // Filter suppliers where is_transporter is checked
                const transporter_suppliers = customer.custom_transporters
                    .filter(row => row.is_transporter)
                    .map(row => row.supplier);
                
                console.log(transporter_suppliers);

                // Find the default supplier with is_transporter checked
                const default_transporter = customer.custom_transporters.find(row => row.is_transporter && row.is_default);

                // Set query for custom_transporter_name field
                frm.set_query('custom_transporter_name', function () {
                    return {
                        filters: {
                            name: ['in', transporter_suppliers]
                        }
                    };
                });

                // Set default value for custom_transporter_name
                if (default_transporter) {
                    frm.set_value('custom_transporter_name', default_transporter.supplier);
                } else if (transporter_suppliers.length > 0) {
                    frm.set_value('custom_transporter_name', transporter_suppliers[0]);
                } else {
                    frm.set_value('custom_transporter_name', null);
                }
            }
        });
    } else {
        // Clear transporter field and reset query
        frm.set_query('custom_transporter_name', function () {
            return {};
        });

        frm.set_value('custom_transporter_name', null);
    }
}




// frappe.ui.form.on('Material Request', {
//     onload: function(frm) {
//         // Filter for custom_shipping_address_name
//         frm.set_query('custom_shipping_address_name', function() {
//             if (!frm.doc.custom_shipping_to) {
//                 return {}; 
//             }
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.custom_shipping_to }
//             };
//         });

//         // Filter for custom_customer_contact
//         frm.set_query('custom_customer_contact', function() {
//             if (!frm.doc.custom_shipping_to) {
//                 return {};
//             }
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.custom_shipping_to }
//             };
//         });
//     }
// });




frappe.ui.form.on('MR Instruction Log Item TH', {
    create_item: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.call({
            method: 'lbf_logistica.overrides.material_request.create_item_from_material_request',
            args: {
                row_data: JSON.stringify(row)
            },
            callback: function (r) {
                if (r.message) {
                    
                    frappe.model.set_value(cdt, cdn, 'item_code', r.message);

                   
                    frm.save();

                   
                    frappe.msgprint(__('Item Created with Item Code: ' + r.message));
                }
            }
        });
    }
});

