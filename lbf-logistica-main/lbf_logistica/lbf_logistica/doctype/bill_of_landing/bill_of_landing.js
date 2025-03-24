// Copyright (c) 2024, Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bill Of Landing', {
    refresh: function(frm) {
        // Bind functionality to the new_address_btn
        frm.fields_dict.new_address_btn.$wrapper.find('button').on('click', function() {
            open_address_dialog(frm, 'Customer', 'new_address');
        });

        // Bind functionality to the new_contact_btn
        frm.fields_dict.new_contact_btn.$wrapper.find('button').on('click', function() {
            open_contact_dialog(frm, 'Customer', 'new_contact');
        });

        // Bind functionality to the new_supplier_address_btn
        frm.fields_dict.new_supplier_address_btn.$wrapper.find('button').on('click', function() {
            open_address_dialog(frm, 'Supplier', 'new_supplier_address');
        });

        // Bind functionality to the new_supplier_contact_btn
        frm.fields_dict.new_supplier_contact_btn.$wrapper.find('button').on('click', function() {
            open_contact_dialog(frm, 'Supplier', 'new_supplier_contact');
        });
        shipping_to_filter(frm);
        customer_party_type_filter(frm);
        // transporter_filter(frm);

        // Add "Create Quality Inspections" button
        if (frm.doc.docstatus === 0 && frm.doc.legal_doc_for_redelivery === 0 && frm.doc.service === 'Peneus Hub') {
            frm.add_custom_button('Quality Inspections for PH', () => {
                frappe.call({
                    method: "lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing.create_quality_inspections",
                    args: {
                        bill_of_lading: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message && response.message.length > 0) {
                            let links = response.message.map(qi => 
                                `<a href="/app/quality-inspection/${qi}" ">${qi}</a>`
                            ).join('<br>');
                            frappe.msgprint({
                                title: __('Quality Inspections Created'),
                                indicator: 'green',
                                message: links
                            });
                        } else {
                            frappe.msgprint(__('Quality Inspections are already created for all items.'));
                        }
                    }
                });
            },__("Create"));
        }
        if (frm.doc.docstatus === 0 && frm.doc.legal_doc_for_redelivery === 0 && frm.doc.service === 'Tyre Hotel') {
            frm.add_custom_button('Quality Inspections for TH', () => {
                frappe.call({
                    method: "lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing.create_quality_inspections",
                    args: {
                        bill_of_lading: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message && response.message.length > 0) {
                            let links = response.message.map(qi => 
                                `<a href="/app/quality-inspection/${qi}" ">${qi}</a>`
                            ).join('<br>');
                            frappe.msgprint({
                                title: __('Quality Inspections Created'),
                                indicator: 'green',
                                message: links
                            });
                        } else {
                            frappe.msgprint(__('Quality Inspections are already created for all items.'));
                        }
                    }
                });
            },__("Create"));
        }
        if (frm.doc.docstatus === 1 && frm.doc.legal_doc_for_redelivery === 0 && frm.doc.stock_entry_created === 0) {
            frm.add_custom_button('Create Stock Entry', () => {
                frappe.call({
                    method: "lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing.create_stock_entry",
                    args: {
                        bill_of_landing: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message && response.message.length > 0) {
                            let links = response.message.map(qi => 
                                `<a href="/app/stock-entry/${qi}" ">${qi}</a>`
                            ).join('<br>');
                            frappe.msgprint({
                                title: __('Stock Entry Created'),
                                indicator: 'green',
                                message: links
                            });
                            frm.reload_doc();
                            
                        } else {
                            frappe.msgprint(__('Stock Entry are already created for all items.'));
                        }
                    }
                });
            },__("Create"));
        }
        const linkStyle = `
            display: inline-flex;
            align-items: center;
            background-color: #f5f5f5;
            border-radius: 12px;
            padding: 5px 10px;
            text-decoration: none;
            font-size: 12px;
            color: #333;
            font-weight: 500;
        `;
        const wrapperStyle = "padding: 10px 0;";
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Quality Inspection",
                filters: { "reference_name": frm.doc.name },
                fields: ["name"]
            },
            callback: function(r) {
                if (r.message) {
                    var quality_inspection = `/app/quality-inspection?reference_name=${frm.doc.name}`;
                    var qa_insp_html = `
                        <div style="${wrapperStyle}">
                            <a href="${quality_inspection}"  style="${linkStyle}"
                               onmouseover="this.style.textDecoration='underline'"
                               onmouseout="this.style.textDecoration='none'">
                                <div style="
                                    border-radius: 10px;
                                    padding: 2px 6px;
                                    margin-right: 8px;
                                    font-size: 12px;
                                    color: #555;
                                    background-color: white;
                                ">
                                    ${r.message.length}
                                </div>
                                Quality Inspections
                            </a>
                        </div>`;
                    frm.set_df_property('qa_insp_html', 'options', qa_insp_html);
                }
            }
        });
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Stock Entry",
                filters: { "custom_bill_of_landing": frm.doc.name },
                fields: ["name"]
            },
            callback: function(r) {
                if (r.message) {
                    var stock_link = `/app/stock-entry?custom_bill_of_landing=${frm.doc.name}`;
                    var stock_entries = `
                        <div style="${wrapperStyle}">
                            <a href="${stock_link}"  style="${linkStyle}"
                               onmouseover="this.style.textDecoration='underline'"
                               onmouseout="this.style.textDecoration='none'">
                                <div style="
                                    border-radius: 10px;
                                    padding: 2px 6px;
                                    margin-right: 8px;
                                    font-size: 12px;
                                    color: #555;
                                    background-color: white;
                                ">
                                    ${r.message.length}
                                </div>
                                Stock Entry
                            </a>
                        </div>`;
                    frm.set_df_property('stock_entries', 'options', stock_entries);
                }
            }
        });




        // Add "Ledger View" button under "View" dropdown when document is submitted
        if (frm.doc.docstatus === 1) { // Check if the document is submitted
            frm.add_custom_button(__('Ledger View'), function () {
                frappe.set_route('query-report', 'Stock Ledger', {
                    voucher_no: frm.doc.name
                });
            }, __('View')); // Add button under "View" dropdown
        }

        // Add "Print Labels" button
        frm.add_custom_button(__('Print Labels'), function() {
            frappe.model.with_doctype(frm.doc.doctype, function() {
                var w = window.open(
                    frappe.urllib.get_full_url(
                        '/printview?doctype=' + 
                        encodeURIComponent(frm.doc.doctype) +
                        '&name=' + 
                        encodeURIComponent(frm.doc.name) +
                        '&trigger_print=1' +
                        '&format=' + 
                        encodeURIComponent('BOL Stickers') +
                        '&no_letterhead=0'
                    )
                );
                if (!w) {
                    frappe.msgprint(__("Please enable pop-ups"));
                }
            });
        });

    },
    customer_address: function(frm) {
        fetch_and_set_address(frm, 'customer_address', 'address');
        if (frm.doc.customer_address) {
            frappe.call({
                method: 'frappe.client.get',
                args: { doctype: 'Address', name: frm.doc.customer_address },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value('customer_name', response.message.address_title || '');
                    }
                }
            });
        } else {
            frm.set_value('customer_name', '');
        }
    },
    service: function (frm) {
        frm.refresh(); 
        if (frm.doc.service === "Peneus Hub") {
            frm.set_value('naming_series', 'MAT-PRE-PH-.YYYY.-.MM.-');
        } else if (frm.doc.service === "Tyre Hotel") {
            frm.set_value('naming_series', 'MAT-PRE-TH-.YYYY.-.MM.-');
        } else {
            frm.set_df_property('naming_series', 'options', '\nMAT-PRE-PH-.YYYY.-.MM.-\nMAT-PRE-TH-.YYYY.-.MM.-');
        }
    },
    party_type: function(frm) {
        customer_party_type_filter(frm);
       
    },
    onload: function(frm) {
        frm.set_query('accepted_warehouse', function () {
            return {
                filters: {
                    custom_type_of_warehouse: ['in', ['Un-Loading Zone', 'Both Loading and Un-Loading Zone']]
                }
            };
        });

    },
    customer: function (frm) {
        shipping_to_filter(frm);
    },
    customer_shipping_address: function (frm) {
        transporter_filter(frm);
    },
    shipping_to: function (frm) {
        if (frm.doc.shipping_to) {
            // Filter Address based on selected Shipment (Customer)
            frm.set_query('customer_address', function () {
                return {
                    filters: {
                        link_doctype: 'Customer',
                        link_name: frm.doc.customer
                    }
                };
            });
            frm.set_query('customer_shipping_address', function () {
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
                        link_name: frm.doc.customer
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
                        ['Dynamic Link', 'link_name', '=', frm.doc.customer]
                    ],
                    // order_by: 'tabAddress.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('customer_address', response.message[0].name);
                    } else {
                        frm.set_value('customer_address', null);
                    }
                }
            });
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
                        frm.set_value('customer_shipping_address', response.message[0].name);
                    } else {
                        frm.set_value('customer_shipping_address', null);
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
                        ['Dynamic Link', 'link_name', '=', frm.doc.customer]
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
            // frm.set_value('customer_address', null);
            frm.set_value('customer_shipping_address', null);
            // frm.set_value('customer_contact', null);
        }
        
    },
    transporter_name: function (frm) {
        if (frm.doc.transporter_name) {
            
            frm.set_query('transporter_address_name', function () {
                return {
                    filters: {
                        link_doctype: 'Supplier',
                        link_name: frm.doc.transporter_name
                    }
                };
            });
            frm.set_query('transporter_contact', function () {
                return {
                    filters: {
                        link_doctype: 'Supplier',
                        link_name: frm.doc.transporter_name
                    }
                };
            });


            
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Address',
                    fields: ['name'],
                    filters: [
                        ['Dynamic Link', 'link_doctype', '=', 'Supplier'],
                        ['Dynamic Link', 'link_name', '=', frm.doc.transporter_name]
                    ],
                    // order_by: 'tabAddress.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('transporter_address_name', response.message[0].name);
                    } else {
                        frm.set_value('transporter_address_name', null);
                    }
                }
            });
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Contact',
                    fields: ['name'],
                    filters: [
                        ['Dynamic Link', 'link_doctype', '=', 'Supplier'],
                        ['Dynamic Link', 'link_name', '=', frm.doc.transporter_name]
                    ],
                    // order_by: 'tabAddress.creation desc',
                    limit_page_length: 1
                },
                callback: function (response) {
                    if (response.message && response.message.length > 0) {
                        frm.set_value('transporter_contact', response.message[0].name);
                    } else {
                        frm.set_value('transporter_contact', null);
                    }
                }
            });

        } else {
            frm.set_value('transporter_address_name', null);
            frm.set_value('transporter_contact', null);
        }
    },
});

function open_address_dialog(frm, link_doctype, html_field) {
    let dialog = new frappe.ui.Dialog({
        title: __('New Address'),
        fields: [
            {fieldname: 'link_doctype', label: 'Link Document Type', fieldtype: 'Link', options: 'DocType', default: link_doctype, reqd: 1},
            {fieldname: 'link_name', label: 'Link Name', fieldtype: 'Link', options: link_doctype, reqd: 1},
            {fieldname: 'gstin_uin', label: 'GSTIN / UIN', fieldtype: 'Data'},
            {fieldname: 'address_type', label: 'Address Type', fieldtype: 'Select', options: ['Billing', 'Shipping'], default: 'Billing', reqd: 1},
            {fieldname: 'gst_category', label: 'GST Category', fieldtype: 'Select', options: ['Registered', 'Unregistered'], default: 'Unregistered', reqd: 1},
            {fieldname: 'postal_code', label: 'Postal Code', fieldtype: 'Data', reqd: 1},
            {fieldname: 'city', label: 'City/Town', fieldtype: 'Data', reqd: 1},
            {fieldname: 'address_line1', label: 'Address Line 1', fieldtype: 'Data', reqd: 1},
            {fieldname: 'state', label: 'State/Province', fieldtype: 'Data', reqd: 1},
            {fieldname: 'country', label: 'Country', fieldtype: 'Data', default: 'India', reqd: 1}
        ],
        primary_action_label: __('Save'),
        primary_action: function(values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Address',
                        address_title: values.link_name,
                        address_type: values.address_type,
                        gst_category: values.gst_category,
                        gstin: values.gstin_uin,
                        address_line1: values.address_line1,
                        city: values.city,
                        state: values.state,
                        country: values.country,
                        pincode: values.postal_code,
                        links: [{
                            link_doctype: values.link_doctype,
                            link_name: values.link_name
                        }]
                    }
                },
                callback: function(response) {
                    if (response.message) {
                        let address = response.message;
                        let formatted_address = `
                        <b>${address.address_title} · ${address.address_type}</b><br>
                        ${address.address_line1}<br>
                        ${address.city}, ${address.state}<br>
                        PIN Code: ${address.pincode}<br>
                        ${address.country}
                        `;
                        frm.fields_dict[html_field].$wrapper.html(formatted_address);
                        frappe.msgprint(__('Address created successfully and displayed below.'));
                        dialog.hide();
                    }
                }
            });
        }
    });

    dialog.show();
}

function open_contact_dialog(frm, link_doctype, html_field) {
    let dialog = new frappe.ui.Dialog({
        title: 'Add New Contact',
        fields: [
            {fieldname: 'first_name', label: 'First Name', fieldtype: 'Data', reqd: 1},
            {fieldname: 'middle_name', label: 'Middle Name', fieldtype: 'Data'},
            {fieldname: 'last_name', label: 'Last Name', fieldtype: 'Data'},
            {
                fieldname: 'email_ids',
                label: 'Email IDs',
                fieldtype: 'Table',
                options: 'Contact Email',
                fields: [
                    {fieldname: 'email_id', label: 'Email ID', fieldtype: 'Data', reqd: 1, "in_list_view": 1},
                    {fieldname: 'is_primary', label: 'Is Primary', fieldtype: 'Check', "in_list_view": 1}
                ]
            },
            {
                fieldname: 'phone_nos',
                label: 'Phone Numbers',
                fieldtype: 'Table',
                options: 'Contact Phone',
                fields: [
                    {fieldname: 'phone', label: 'Number', fieldtype: 'Data', reqd: 1, "in_list_view": 1},
                    {fieldname: 'is_primary_phone', label: 'Is Primary Phone', fieldtype: 'Check', "in_list_view": 1},
                    {fieldname: 'is_primary_mobile_no', label: 'Is Primary Mobile', fieldtype: 'Check', "in_list_view": 1}
                ]
            },
            {fieldname: 'link_name', label: link_doctype, fieldtype: 'Link', options: link_doctype, reqd: 1, default: frm.doc[link_doctype.toLowerCase()]}
        ],
        primary_action_label: 'Save Contact',
        primary_action: function(values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Contact',
                        first_name: values.first_name,
                        middle_name: values.middle_name,
                        last_name: values.last_name,
                        email_ids: values.email_ids.map(row => ({
                            email_id: row.email_id,
                            is_primary: row.is_primary
                        })),
                        phone_nos: values.phone_nos.map(row => ({
                            phone: row.phone,
                            is_primary_phone: row.is_primary_phone,
                            is_primary_mobile_no: row.is_primary_mobile_no
                        })),
                        links: [
                            {
                                link_doctype: link_doctype,
                                link_name: values.link_name
                            }
                        ]
                    }
                },
                callback: function(response) {
                    if (response.message) {
                        let contact = response.message;
                        let formatted_contact = `
                        <b>${contact.first_name || ''} ${contact.middle_name || ''} ${contact.last_name || ''}</b><br>
                        ${contact.phone_nos
                            .map(p => `${p.phone} ${p.is_primary_phone ? '· Primary Phone' : ''} ${p.is_primary_mobile ? '· Primary Mobile' : ''}`)
                            .join('<br>')}<br>
                        ${contact.email_ids
                            .map(e => `${e.email_id} ${e.is_primary ? '· Primary Email' : ''}`)
                            .join('<br>')}<br>
                        ${frm.doc[link_doctype.toLowerCase()] || ''}
                    `;
                        frm.fields_dict[html_field].$wrapper.html(formatted_contact);
                        frappe.msgprint(__('Contact created successfully!'));
                        dialog.hide();
                    }
                }
            });
        }
    });

    dialog.show();
}


// frappe.ui.form.on('Bill Of Landing', {
//     onload: function(frm) {
//         // Apply filters for Customer fields
//         frm.set_query('customer_address', function() {
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.shipping_to }
//             };
//         });

//         frm.set_query('customer_shipping_address', function() {
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.shipping_to }
//             };
//         });

//         frm.set_query('customer_contact', function() {
//             return {
//                 filters: { link_doctype: 'Customer', link_name: frm.doc.shipping_to}
//             };
//         });

//         // Apply filters for Supplier (Transporter) fields
//         frm.set_query('transporter_address_name', function() {
//             return {
//                 filters: { link_doctype: 'Supplier', link_name: frm.doc.transporter_name , custom_transporter_address:1 }
//             };
//         });
        
//         frm.set_query('transporter_contact', function() {
//             return {
//                 filters: { link_doctype: 'Supplier', link_name: frm.doc.transporter_name ,custom_transporter_contact:1}
//             };
//         });
//     },

   

//     customer_shipping_address: function(frm) {
//         fetch_and_set_address(frm, 'customer_shipping_address', 'shipping_address');
//     },

//     customer_contact: function(frm) {
//         fetch_and_set_contact(frm, 'customer_contact', 'contact');
//         if (frm.doc.customer_contact) {
//             frappe.call({
//                 method: 'frappe.client.get',
//                 args: { doctype: 'Contact', name: frm.doc.customer_contact },
//                 callback: function(response) {
//                     if (response.message) {
//                         let contact = response.message;
//                         let full_name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
//                         frm.set_value('contact_person', full_name || '');
//                     }
//                 }
//             });
//         } else {
//             frm.set_value('contact_person', '');
//         }
//     },

//     shipping_contact_person: function(frm) {
//         fetch_and_set_contact(frm, 'shipping_contact_person', 'shiping_contact');
//     },

//     transporter_address_name: function(frm) {
//         fetch_and_set_address(frm, 'transporter_address_name', 'transporter_address');
//         if (frm.doc.transporter_address_name) {
//             frappe.call({
//                 method: 'frappe.client.get',
//                 args: { doctype: 'Address', name: frm.doc.transporter_address_name },
//                 callback: function(response) {
//                     console.log(response.message)
//                     console.log(response.message.address_title)
//                     console.log(response.message)
//                     if (response.message) {
//                         frm.set_value('transporter_address', response.message.address_title || '');
//                     }
//                 }
//             });
//         } else {
//             frm.set_value('transporter_address', '');
//         }
//     },

//     transporter_contact: function(frm) {
//         fetch_and_set_contact(frm, 'transporter_contact', 'transport_contact');
//         if (frm.doc.transporter_contact) {
//             frappe.call({
//                 method: 'frappe.client.get',
//                 args: { doctype: 'Contact', name: frm.doc.transporter_contact },
//                 callback: function(response) {
//                     if (response.message) {
//                         let contact = response.message;
//                         let full_name = [contact.first_name, contact.last_name].filter(Boolean).join(' ');
//                         frm.set_value('transporter_contact_person', full_name || '');
//                     }
//                 }
//             });
//         } else {
//             frm.set_value('transporter_contact_person', '');
//         }
//     }
// });

function fetch_and_set_address(frm, address_field, target_field) {
    if (frm.doc[address_field]) {
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Address', name: frm.doc[address_field] },
            callback: function(response) {
                if (response.message) {
                    let address = response.message;
                    let formatted_address = `${address.address_title || ''} · ${address.address_type || ''}
${address.address_line1 || ''}
${address.city || ''}, ${address.state || ''}
PIN Code: ${address.pincode || ''}
${address.country || ''}`;
                    frm.set_value(target_field, formatted_address);
                }
            }
        });
    } else {
        frm.set_value(target_field, '');
    }
}

function fetch_and_set_contact(frm, contact_field, target_field) {
    if (frm.doc[contact_field]) {
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Contact', name: frm.doc[contact_field] },
            callback: function(response) {
                if (response.message) {
                    let contact = response.message;
                    let primary_phone = (contact.phone_nos || []).find(phone => phone.is_primary_phone);
                    frm.set_value(target_field, primary_phone ? primary_phone.phone : 'No primary phone available');
                }
            }
        });
    } else {
        frm.set_value(target_field, '');
    }
}

function customer_party_type_filter(frm) {
    if (frm.doc.party_type) {
        frm.set_query('customer', function() {
            return {
                filters: {
                    customer_group: frm.doc.party_type
                }
            };
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

function transporter_filter(frm){
    if (frm.doc.customer_shipping_address) {
        frappe.db.get_doc('Address', frm.doc.customer_shipping_address).then((customer) => {
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



frappe.ui.form.on('Bill of Landing Items TH', {
    tyre_type: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn]; 
        if (!row.tyre_type) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Tyre Hotel Pricing Rule",
                name: frm.doc.customer
            },
            callback: function (r) {
                if (r.message) {
                    let rate = 0;

                    if (row.tyre_type === "With Rim") {
                        rate = r.message.amount_with_rim;
                    } else if (row.tyre_type === "Without Rim") {
                        rate = r.message.amount_without_rim;
                    }

                    let updated = false;
                    frm.doc.th_charges.forEach((charge_row) => {
                        if (
                            charge_row.item_name === row.item_name && 
                            charge_row.idx === row.idx 
                        ) {
                            charge_row.tyre_type = row.tyre_type;
                            charge_row.qty = row.qty;
                            charge_row.rate = rate;
                            charge_row.amount = row.qty * rate; 
                            updated = true; 
                        }
                    });

                    if (!updated && rate) {
                        let th_charges_row = frm.add_child("th_charges");
                        th_charges_row.item_name = row.item_name;
                        th_charges_row.item_code = row.item_code;
                        th_charges_row.tyre_type = row.tyre_type;
                        th_charges_row.qty = row.qty;
                        th_charges_row.rate = rate;
                        th_charges_row.amount = row.qty * rate; 
                    }

                    frm.refresh_field("th_charges"); 
                }
            }
        });
    }
});


























// frappe.ui.form.on('Bill Of Landing', {
//     refresh: function(frm) {
//         frm.add_custom_button(__('Generate PNR'), function() {
//             window.open(
//                 `/api/method/lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing.generate_pnr?docname=${frm.doc.name}`
//             );
//         });
//     }
// });



// lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing

frappe.ui.form.on('Bill Of Landing', {
    refresh: function(frm) {
        // Add button for Peneus Hub labels
        if(frm.doc.service === "Peneus Hub" && frm.doc.item_details_ph && frm.doc.item_details_ph.length > 0) {
            frm.add_custom_button(__('Print Peneus Hub Labels'), function() {
                const args = {
                    doctype: frm.doctype,
                    docname: frm.docname,
                    service_type: "Peneus Hub"
                };
                const url = frappe.urllib.get_full_url(
                    `/api/method/lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing.print_labels?` +
                    `doctype=${encodeURIComponent(args.doctype)}&` +
                    `docname=${encodeURIComponent(args.docname)}&` +
                    `service_type=${encodeURIComponent(args.service_type)}`
                );
                window.open(url);
            }, __('Generate Prn File'));
        }
        
        // Add button for Tyre Hotel labels
        if(frm.doc.service === "Tyre Hotel" && frm.doc.item_details_th && frm.doc.item_details_th.length > 0) {
            frm.add_custom_button(__('Print Tyre Hotel Labels'), function() {
                const args = {
                    doctype: frm.doctype,
                    docname: frm.docname,
                    service_type: "Tyre Hotel"
                };
                const url = frappe.urllib.get_full_url(
                    `/api/method/lbf_logistica.lbf_logistica.doctype.bill_of_landing.bill_of_landing.print_labels?` +
                    `doctype=${encodeURIComponent(args.doctype)}&` +
                    `docname=${encodeURIComponent(args.docname)}&` +
                    `service_type=${encodeURIComponent(args.service_type)}`
                );
                window.open(url);
            }, __('Generate Prn File'));
        }
    }
});

