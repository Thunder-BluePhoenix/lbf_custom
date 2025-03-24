// Copyright (c) 2025, Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Invoice Log", {
	// refresh(frm) {

	// },

    service: function (frm) {
        frm.refresh(); 
        if (frm.doc.service === "Peneus Hub") {
            frm.set_value('naming_series', "PH-BL-.YYYY.-.MM.-");
        } else if (frm.doc.service === "Tyre Hotel") {
            frm.set_value('naming_series', "TH-BL-.YYYY.-.MM.-");
        } 
    }
});



frappe.ui.form.on("Bulk Invoice Log", {
    get_customers: function(frm) {
        open_customer_selection_popup(frm);
    }
 });

 function open_customer_selection_popup(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Customer',
            fields: ['name', 'customer_name']
        },
        callback: function(response) {
            if (response.message) {
                let customers = response.message;
                let existing_customers = (frm.doc.customer_details || []).map(row => row.customer);
                
                let html_content = `
                    <div class="customer-selection-container">
                        <div class="row">
                            <div class="col-md-6">
                                <h4>All Customers</h4>
                                <input type="text" class="form-control mb-2" id="customer-search" placeholder="Search customers...">
                                <div class="mb-2">
                                    <input type="checkbox" id="select-all-customers"> <label for="select-all-customers">Select All</label>
                                </div>
                                <div style="max-height: 400px; overflow-y: auto;">
                                    <table class="table table-bordered" id="all-customers-table">
                                        <thead>
                                            <tr><th>Select</th><th>Customer Name</th></tr>
                                        </thead>
                                        <tbody>
                                            ${customers.map(c => `
                                                <tr>
                                                    <td><input type="checkbox" class="customer-checkbox" data-name="${c.name}" data-customer-name="${c.customer_name}" ${existing_customers.includes(c.name) ? 'checked' : ''}></td>
                                                    <td>${c.customer_name}</td>
                                                </tr>`).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h4>Selected Customers</h4>
                                <div style="max-height: 400px; overflow-y: auto;">
                                    <table class="table table-bordered" id="selected-customers-table">
                                        <thead>
                                            <tr><th>Customer Name</th></tr>
                                        </thead>
                                        <tbody>
                                            ${existing_customers.length ? existing_customers.map(c => `<tr><td>${c}</td></tr>`).join('') : '<tr><td class="text-center">No Data</td></tr>'}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                let customer_dialog = new frappe.ui.Dialog({
                    title: __('Select Customers'),
                    size: 'large',
                    fields: [{ fieldtype: 'HTML', fieldname: 'customer_selection_html', options: html_content }]
                });
                
                customer_dialog.show();
                
                setTimeout(() => {
                    $('#customer-search').on('keyup', function() {
                        let value = $(this).val().toLowerCase();
                        $('#all-customers-table tbody tr').filter(function() {
                            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
                        });
                    });
                    
                    $('#select-all-customers').on('click', function() {
                        let is_checked = $(this).prop('checked');
                        $('.customer-checkbox').prop('checked', is_checked).trigger('change');
                    });
                    
                    $('.customer-checkbox').each(function() {
                        let customer_name = $(this).data('customer-name');
                        if ($(this).is(':checked')) {
                            move_customer_to_table(customer_name, 'selected-customers-table');
                        }
                    });
                    
                    $('.customer-checkbox').on('change', function() {
                        let customer_name = $(this).data('customer-name');
                        if ($(this).is(':checked')) {
                            move_customer_to_table(customer_name, 'selected-customers-table');
                        } else {
                            remove_customer_from_table(customer_name, 'selected-customers-table');
                        }
                    });
                }, 500);
                
                customer_dialog.set_primary_action(__('Proceed'), function() {
                    frm.set_value('customer_details', null)
                    let selected_customers = get_customers_from_table('selected-customers-table');
                    let customer_details = selected_customers.map(customer => ({ customer }));
                    frm.set_value('customer_details', customer_details);
                    frm.refresh_field('customer_details');
                    customer_dialog.hide();
                });
            }
        }
    });
}

function move_customer_to_table(customer_name, table_id) {
    let table_body = $('#' + table_id + ' tbody');
    if (table_body.find('tr td.text-center').length) {
        table_body.empty();
    }
    if (!table_body.find(`tr:contains('${customer_name}')`).length) {
        table_body.append(`<tr><td>${customer_name}</td></tr>`);
    }
}

function remove_customer_from_table(customer_name, table_id) {
    let table_body = $('#' + table_id + ' tbody');
    table_body.find('tr').filter(function() {
        return $(this).find('td:first').text().trim() === customer_name;
    }).remove();
    if (!table_body.find('tr').length) {
        table_body.append('<tr><td class="text-center">No Data</td></tr>');
    }
}

function get_customers_from_table(table_id) {
    return $('#' + table_id + ' tbody tr').map(function() {
        let cell_text = $(this).find('td:first').text().trim();
        return cell_text === 'No Data' ? null : cell_text;
    }).get().filter(Boolean);
}




frappe.ui.form.on("Bulk Invoice Log", {
    submit_invoices: function(frm) {
        submit_invoices(frm);
    }
 });


 function submit_invoices(frm) {
    frappe.call({
        method:"lbf_logistica.lbf_logistica.doctype.bulk_invoice_log.bulk_invoice_log.submit_invoices",
        args:{
            docname: frm.doc.name
        },
        callback: function(response){
            frm.reload_doc();
        }
    })
 }

