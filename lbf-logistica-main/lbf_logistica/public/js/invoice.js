frappe.ui.form.on('Sales Invoice', {
    // Trigger when customer is selected
    customer: function (frm) {
        if (frm.doc.custom_peneus_hub) {
            populate_custom_fields(frm);
            // populate_table_fields(frm);
        }
    },
    
    // Trigger when custom_peneus_hub is checked
    custom_peneus_hub: function (frm) {
        if (frm.doc.customer) {
            populate_custom_fields(frm);
            // populate_table_fields(frm);
        }
    }
});

function populate_custom_fields(frm) {
    if (!frm.doc.customer || !frm.doc.custom_peneus_hub) {
        return;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Pricing Rule',
            filters: { custom_customerr: frm.doc.customer },
            fields: [
                'custom_handling_in', 
                'custom_amount_handling_in', 
                'custom_handling_out', 
                'custom_amount_handling_out', 
                'custom_amount_cost_over_time_charges', 
                'custom_currencycost_over_time_charges'
            ]
        },
        callback: function (response) {
            let pricing_rules = response.message;
            if (pricing_rules && pricing_rules.length > 0) {
                let pricing_rule = pricing_rules[0];
                frm.set_value('custom_handling_in_charges', pricing_rule.custom_handling_in ? pricing_rule.custom_amount_handling_in : 0);
                frm.set_value('custom_handling_out_charges', pricing_rule.custom_handling_out ? pricing_rule.custom_amount_handling_out : 0);
                frm.set_value('custom_storage_rate_per_day', pricing_rule.custom_amount_cost_over_time_charges);
                frm.set_value('custom_lbf_currency', pricing_rule.custom_currencycost_over_time_charges);
                frm.refresh_fields();
            }
        }
    });
}

// function populate_table_fields(frm) {
//     if (!frm.doc.customer || !frm.doc.custom_peneus_hub) {
//         return;
//     }

//     // Clear existing table rows
//     frm.clear_table('custom_storage_fees_for_items');

//     // Fetch previous invoices
//     frappe.call({
//         method: 'frappe.client.get_list',
//         args: {
//             doctype: 'Sales Invoice',
//             filters: {
//                 'customer': frm.doc.customer,
//                 'custom_peneus_hub': 1,
//                 'docstatus': 1
//             },
//             order_by: 'creation desc',
//             limit: 1
//         },
//         callback: function(previous_invoices_response) {
//             // Fetch Bill of Landings
//             frappe.call({
//                 method: 'frappe.client.get_list',
//                 args: {
//                     doctype: 'Bill Of Landing',
//                     filters: {
//                         'customer': frm.doc.customer,
//                         'service': 'Peneus hub',
//                         'docstatus': 1
//                     },
//                     order_by: 'creation',
//                     fields: ['name', 'creation', 'total_qty_accepted']
//                 },
//                 callback: function(bill_of_landings_response) {
//                     // Fetch Pick Lists
//                     frappe.call({
//                         method: 'frappe.client.get_list',
//                         args: {
//                             doctype: 'Pick List',
//                             filters: {
//                                 'custom_pl_customer': frm.doc.customer,
//                                 'custom_service': 'Peneus hub',
//                                 'docstatus': 1
//                             },
//                             order_by: 'creation',
//                             fields: ['name', 'creation', 'custom_item_qty']
//                         },
//                         callback: function(pick_lists_response) {
//                             let bill_of_landings = bill_of_landings_response.message || [];
//                             let pick_lists = pick_lists_response.message || [];
//                             let previous_invoices = previous_invoices_response.message || [];

//                             // Determine base date for filtering
//                             let base_date = previous_invoices.length > 0 
//                                 ? frappe.datetime.str_to_obj(previous_invoices[0].posting_date)
//                                 : null;

//                             // Filter documents based on base date
//                             let filtered_bill_of_landings = base_date
//                                 ? bill_of_landings.filter(bl => 
//                                     frappe.datetime.get_diff(frappe.datetime.str_to_obj(bl.creation), base_date) > 0
//                                 )
//                                 : bill_of_landings;

//                             let filtered_pick_lists = base_date
//                                 ? pick_lists.filter(pl => 
//                                     frappe.datetime.get_diff(frappe.datetime.str_to_obj(pl.creation), base_date) > 0
//                                 )
//                                 : pick_lists;

//                             // Combine and sort documents
//                             let combined_docs = [];
//                             let used_bill_of_landings = new Set();
//                             let used_pick_lists = new Set();

//                             // Add Bill of Landings
//                             filtered_bill_of_landings.forEach(bl => {
//                                 if (!used_bill_of_landings.has(bl.name)) {
//                                     combined_docs.push({
//                                         type: 'Bill Of Landing',
//                                         doc: bl,
//                                         creation: bl.creation,
//                                         received_qty: bl.total_qty_accepted,
//                                         sold_qty: 0
//                                     });
//                                     used_bill_of_landings.add(bl.name);
//                                 }
//                             });

//                             // Add Pick Lists
//                             filtered_pick_lists.forEach(pl => {
//                                 if (!used_pick_lists.has(pl.name)) {
//                                     combined_docs.push({
//                                         type: 'Pick List',
//                                         doc: pl,
//                                         creation: pl.creation,
//                                         sold_qty: pl.custom_item_qty,
//                                         received_qty: 0
//                                     });
//                                     used_pick_lists.add(pl.name);
//                                 }
//                             });

//                             // Sort combined documents by creation date
//                             combined_docs.sort((a, b) => new Date(a.creation) - new Date(b.creation));

//                             // Initial running final quantity
//                             let running_final_qty = base_date 
//                                 ? parseFloat(frm.doc.custom_storage_fees_for_items?.[frm.doc.custom_storage_fees_for_items.length - 1]?.final_qty || 0)
//                                 : 0;

//                             let today = frappe.datetime.get_today();

//                             // Process documents and populate table
//                             combined_docs.forEach((doc_entry, index) => {
//                                 let new_row = frm.add_child('custom_storage_fees_for_items');
                                
//                                 // Set basic details
//                                 new_row.date = frappe.datetime.str_to_obj(doc_entry.creation).toISOString().split('T')[0];
                                
//                                 if (doc_entry.type === 'Bill Of Landing') {
//                                     new_row.bill_of_landing = doc_entry.doc.name;
//                                     new_row.received_qty = doc_entry.received_qty;
                                    
//                                     // Find matching Pick List
//                                     let matching_pick_list = filtered_pick_lists.find(pl => 
//                                         frappe.datetime.str_to_obj(pl.creation).toISOString().split('T')[0] === new_row.date && 
//                                         !used_pick_lists.has(pl.name)
//                                     );
                                    
//                                     if (matching_pick_list) {
//                                         new_row.pick_list = matching_pick_list.name;
//                                         new_row.sold_qty = matching_pick_list.custom_item_qty;
//                                         used_pick_lists.add(matching_pick_list.name);
//                                     } else {
//                                         new_row.sold_qty = 0;
//                                     }
//                                 } else {
//                                     new_row.pick_list = doc_entry.doc.name;
//                                     new_row.sold_qty = doc_entry.sold_qty;
                                    
//                                     // Find matching Bill of Landing
//                                     let matching_bill_of_landing = filtered_bill_of_landings.find(bl => 
//                                         frappe.datetime.str_to_obj(bl.creation).toISOString().split('T')[0] === new_row.date && 
//                                         !used_bill_of_landings.has(bl.name)
//                                     );
                                    
//                                     if (matching_bill_of_landing) {
//                                         new_row.bill_of_landing = matching_bill_of_landing.name;
//                                         new_row.received_qty = matching_bill_of_landing.total_qty_accepted;
//                                         used_bill_of_landings.add(matching_bill_of_landing.name);
//                                     } else {
//                                         new_row.received_qty = 0;
//                                     }
//                                 }

//                                 // Calculate final quantity
//                                 running_final_qty += parseFloat(new_row.received_qty) - parseFloat(new_row.sold_qty);
//                                 new_row.final_qty = running_final_qty;

//                                 // Calculate number of days
//                                 let current_date = frappe.datetime.str_to_obj(new_row.date);
//                                 let next_date = index < combined_docs.length - 1 
//                                     ? frappe.datetime.str_to_obj(combined_docs[index + 1].creation) 
//                                     : frappe.datetime.str_to_obj(today);
                                
//                                 new_row.number_of_days = frappe.datetime.get_diff(next_date, current_date);

//                                 // Calculate financial details
//                                 new_row.daily_rate = frm.doc.custom_storage_rate_per_day;
//                                 new_row.daily_sub_total = new_row.final_qty * new_row.daily_rate;
//                                 new_row.cost_for_the_days = new_row.number_of_days * new_row.daily_sub_total;
//                                 new_row.handling_in_charges = parseFloat(new_row.received_qty) * parseFloat(frm.doc.custom_handling_in_charges);
//                                 new_row.handling_out_charges = parseFloat(new_row.sold_qty) * parseFloat(frm.doc.custom_handling_out_charges);
//                                 new_row.amount = new_row.cost_for_the_days + new_row.handling_in_charges + new_row.handling_out_charges;
//                             });

//                             // Calculate total amounts
//                             let total_amount = frm.doc.custom_storage_fees_for_items.reduce((sum, row) => sum + row.amount, 0);

//                             frm.set_value('custom_total_cost', total_amount);
//                             frm.set_value('custom_grand_total_cost', total_amount);
//                             // frm.set_value('custom_total_in_words', frappe.utils.money_in_words(total_amount));

//                             frm.refresh_field('custom_storage_fees_for_items');
//                         }
//                     });
//                 }
//             });
//         }
//     });
// }

frappe.ui.form.on('Sales Invoice', {
    customer: function (frm) {
        if (frm.doc.custom_peneus_hub) {
            fetch_last_invoice_and_update_date(frm, 'custom_peneus_hub');
        }
        if (frm.doc.custom_tyre_hotel) {
            fetch_tyre_hotel_data_and_update(frm);
        }
    },

    custom_peneus_hub: function (frm) {
        if (frm.doc.customer) {
            fetch_last_invoice_and_update_date(frm, 'custom_peneus_hub');
        }
    },

    custom_tyre_hotel: function (frm) {
        if (frm.doc.customer) {
            fetch_tyre_hotel_data_and_update(frm);
        }
    }
});

function fetch_last_invoice_and_update_date(frm, mode) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Sales Invoice',
            filters: {
                customer: frm.doc.customer,
                [mode]: 1,
                docstatus: 1
            },
            fields: ['name', 'custom_end_date_for_storage_cost']
        },
        callback: function (response) {
            if (response.message && response.message.length > 0) {
                let last_invoice = response.message[0];

                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Sales Invoice',
                        name: last_invoice.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            let invoice = r.message;
                            if (invoice.custom_storage_fees_for_items && invoice.custom_storage_fees_for_items.length > 0) {
                                // Access the last row's date
                                let prev_date = invoice.custom_end_date_for_storage_cost;
                                
                                if (prev_date) {
                                    let prevDateObj = new Date(prev_date); // Convert to Date object
                                    prevDateObj.setDate(prevDateObj.getDate() + 1); // Add 1 day
                                    let last_date = prevDateObj.toISOString().split('T')[0]; // Format as YYYY-MM-DD

                                    // Set start date based on mode
                                    if (mode === 'custom_peneus_hub') {
                                        frm.set_value('custom_start_date_for_storage_cost_', last_date);
                                        console.log("Updated custom_start_date_for_storage_cost_ for Peneus Hub with:", last_date);
                                    }
                                } else {
                                    console.error("Previous date is not defined");
                                }
                            }
                        }
                    }
                });
            }
        }
    });
}



function fetch_tyre_hotel_data_and_update(frm) {
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Tyre Hotel Pricing Rule',
            name: frm.doc.custom_customerr,
            fieldname: ['amount_with_rim', 'amount_without_rim', 'minimum_threshold_days']
        },
        callback: function (response) {
            if (response.message) {
                frm.set_value('custom_charges_with_rim', response.message.amount_with_rim);
                frm.set_value('custom_charges_without_rim', response.message.amount_without_rim);
                frm.set_value('custom_minimum_threshold_days', response.message.minimum_threshold_days);

                console.log("Tyre Hotel Settings applied:", response.message);

                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Sales Invoice',
                        filters: {
                            customer: frm.doc.customer,
                            custom_tyre_hotel: 1,
                            docstatus: 1
                        },
                        fields: ['name', 'posting_date']
                    },
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            let last_invoice = r.message[0];

                            frappe.call({
                                method: 'frappe.client.get',
                                args: {
                                    doctype: 'Sales Invoice',
                                    name: last_invoice.name
                                },
                                callback: function (r) {
                                    if (r.message) {
                                        let invoice = r.message;
                                        if (invoice.custom_storage_fees_for_items && invoice.custom_storage_fees_for_items.length > 0) {

                                            let last_row = invoice.custom_storage_fees_for_items[invoice.custom_storage_fees_for_items.length - 1];
                                            let prev_date = last_row.date;

                                            if (prev_date) {
                                                let prevDateObj = new Date(prev_date); // Convert to Date object
                                                prevDateObj.setDate(prevDateObj.getDate() + 1); // Add 1 day
                                                let last_date = prevDateObj.toISOString().split('T')[0]; // Format as YYYY-MM-DD

                                                frm.set_value('custom_start_date_for_tyre_hotel_', last_date);
                                                console.log("Updated custom_start_date_for_tyre_hotel_ with:", last_date);
                                            } else {
                                                console.error("Previous date is not defined in last row");
                                            }
                                        }
                                    }
                                }
                            });
                        }
                    }
                });
            }
        }
    });
}


