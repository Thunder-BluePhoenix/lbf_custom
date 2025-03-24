frappe.ui.form.on('Quality Inspection', {
    refresh: function(frm) {
        frm.set_query('item_code', function() {
            return {}; 
        });
    }
});



frappe.ui.form.on('Quality Inspection', {
    custom_select_accepted_and_rejected_serial_nos_: function(frm) {
        open_item_selection_popup(frm);
    }
 });
 
 function open_item_selection_popup(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Select Procedure'),
        size: 'small',
        fields: [
            { label: __('Scan'), fieldname: 'scan_button', fieldtype: 'Button' },
            { fieldtype: 'Column Break' },
            { label: __('Bulk Select'), fieldname: 'bulk_select_button', fieldtype: 'Button' }
        ]
    });
 
    dialog.get_field('bulk_select_button').$wrapper.on('click', function() {
        dialog.hide();
        open_bulk_select_popup(frm);
    });

    dialog.get_field('scan_button').$wrapper.on('click', function() {
        // dialog.hide();
        // open_bulk_select_popup(frm);
        frappe.msgprint(__('Scan functionality coming soon!'));
    });
 
    dialog.show();
 }
 
 function open_bulk_select_popup(frm) {
    frappe.call({
        method: 'frappe.client.get',
        args: { doctype: 'Serial and Batch Bundle', name: frm.doc.custom_serial_and_batch_bundle_id },
        callback: function(response) {
            if (response.message) {
                let bundle_doc = response.message;
                let all_serials = bundle_doc.entries.map(entry => entry.serial_no);
                let bundle_id = frm.doc.custom_serial_and_batch_bundle_id;
 
                // Get existing accepted & rejected serials
                let accepted_serials = (frm.doc.custom_accepted_serial_nos || "").split("\n").filter(Boolean);
                let rejected_serials = (frm.doc.custom_rejected_serial_nos || "").split("\n").filter(Boolean);
 
                let html_content = `
                    <div class="serial-selection-container">
                        <h4 class="mb-3">Serial and Batch Bundle ID: <b>${bundle_id}</b></h4>
 
                        <div class="row">
                            <div class="col-md-12 mb-4">
                                <h4>All Serial Numbers</h4>
                                <div class="form-group mb-2">
                                    <input type="text" class="form-control" id="serial-search" placeholder="Search serial numbers...">
                                </div>
                                <div class="mb-2">
                                    <div class="d-flex align-items-center mb-2">
                                        <div class="mr-2"><input type="checkbox" id="select-all"></div>
                                        <div><label for="select-all" class="mb-0 ml-1">Select All</label></div>
                                    </div>
                                    <div class="status-indicators d-flex flex-wrap mb-2">
                                        <div class="mr-3"><span class="badge badge-success" style="font-size: 14px; padding: 5px 10px;">Accepted</span></div>
                                        <div class="mr-3"><span class="badge badge-danger" style="font-size: 14px; padding: 5px 10px;">Rejected</span></div>
                                        <div><span class="badge badge-light" style="font-size: 14px; padding: 5px 10px;">Not Selected</span></div>
                                    </div>
                                </div>
                                <div style="max-height: 400px; overflow-y: auto;">
                                    <table class="table table-bordered table-sm" id="all-serials-table">
                                        <thead>
                                            <tr>
                                                <th style="width: 40px;"><input type="checkbox" id="select-all-table"></th>
                                                <th>Serial No</th>
                                                <th style="width: 150px;">Status</th>
                                                <th style="width: 180px;">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${all_serials.map(serial => {
                                                let status = "";
                                                let status_class = "";
                                                if (accepted_serials.includes(serial)) {
                                                    status = "Accepted";
                                                    status_class = "badge-success";
                                                } else if (rejected_serials.includes(serial)) {
                                                    status = "Rejected";
                                                    status_class = "badge-danger";
                                                } else {
                                                    status = "Not Selected";
                                                    status_class = "badge-light";
                                                }
                                                return `<tr>
                                                    <td><input type="checkbox" class="serial-checkbox" data-serial="${serial}"></td>
                                                    <td>${serial}</td>
                                                    <td><span class="badge ${status_class} status-badge" style="font-size: 14px; padding: 5px 10px; width: 100%; display: inline-block; text-align: center;">${status}</span></td>
                                                    <td>
                                                        <div class="d-flex">
                                                            <button class="btn btn-success btn-xs mr-2 accept-btn" data-serial="${serial}">Accept</button>
                                                            <button class="btn btn-danger btn-xs reject-btn" data-serial="${serial}">Reject</button>
                                                        </div>
                                                    </td>
                                                </tr>`;
                                            }).join('')}
                                        </tbody>
                                    </table>
                                </div>
                                <div class="mt-3 d-flex">
                                    <button class="btn btn-success btn-sm mr-2" id="accept-selected">Accept Selected</button>
                                    <button class="btn btn-danger btn-sm" id="reject-selected">Reject Selected</button>
                                </div>
                            </div>
                        </div>
 
                        <div class="row mt-4">
                            <div class="col-md-6 mb-4">
                                <h4>Accepted Serial Numbers</h4>
                                <div style="max-height: 400px; overflow-y: auto;">
                                    <table class="table table-bordered table-sm" id="accepted-serials-table">
                                        <thead><tr><th>Serial No</th></tr></thead>
                                        <tbody>
                                            ${accepted_serials.length ? accepted_serials.map(serial => `<tr><td>${serial}</td></tr>`).join('') : '<tr><td class="text-center">No Data</td></tr>'}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
 
                            <div class="col-md-6 mb-4">
                                <h4>Rejected Serial Numbers</h4>
                                <div style="max-height: 400px; overflow-y: auto;">
                                    <table class="table table-bordered table-sm" id="rejected-serials-table">
                                        <thead><tr><th>Serial No</th></tr></thead>
                                        <tbody>
                                            ${rejected_serials.length ? rejected_serials.map(serial => `<tr><td>${serial}</td></tr>`).join('') : '<tr><td class="text-center">No Data</td></tr>'}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
 
                let bulk_select_dialog = new frappe.ui.Dialog({
                    title: __('Bulk Select Serial Numbers'),
                    size: 'extra-large',
                    fields: [
                        { fieldtype: 'HTML', fieldname: 'serial_selection_html', options: html_content }
                    ]
                });
 
                bulk_select_dialog.show();
 
                setTimeout(() => {
                    // Sync both select-all checkboxes
                    $('#select-all, #select-all-table').on('click', function() {
                        let is_checked = $(this).prop('checked');
                        $('#select-all, #select-all-table').prop('checked', is_checked);
                        $('.serial-checkbox').prop('checked', is_checked);
                    });
 
                    // Search functionality
                    $('#serial-search').on('keyup', function() {
                        let value = $(this).val().toLowerCase();
                        $('#all-serials-table tbody tr').filter(function() {
                            let serial = $(this).find('td:nth-child(2)').text().toLowerCase();
                            $(this).toggle(serial.indexOf(value) > -1);
                        });
                    });
 
                    // Bulk selection handlers
                    $('#accept-selected').on('click', function() {
                        handle_bulk_selection(true);
                        update_status_badges();
                    });
 
                    $('#reject-selected').on('click', function() {
                        handle_bulk_selection(false);
                        update_status_badges();
                    });
 
                    // Individual item action handlers
                    $('.accept-btn').on('click', function() {
                        let serial = $(this).data('serial');
                        move_serial_to_table(serial, 'accepted-serials-table');
                        remove_serial_from_table(serial, 'rejected-serials-table');
                        update_status_badges();
                    });
 
                    $('.reject-btn').on('click', function() {
                        let serial = $(this).data('serial');
                        move_serial_to_table(serial, 'rejected-serials-table');
                        remove_serial_from_table(serial, 'accepted-serials-table');
                        update_status_badges();
                    });
 
                }, 500);
 
                // Proceed Button - Save to form fields
                
                bulk_select_dialog.set_primary_action(__('Proceed'), function() {
                    let accepted_serials = get_serials_from_table('accepted-serials-table').join('\n');
                    let rejected_serials = get_serials_from_table('rejected-serials-table').join('\n');

                    let accepted_count = accepted_serials ? accepted_serials.split('\n').length : 0;
                    let rejected_count = rejected_serials ? rejected_serials.split('\n').length : 0;

                    frm.set_value('custom_accepted_serial_nos', accepted_serials);
                    frm.set_value('custom_rejected_serial_nos', rejected_serials);
                    frm.set_value('custom_accepted_qty', accepted_count);
                    frm.set_value('custom_rejected_qty', rejected_count);

                    bulk_select_dialog.hide();
                    frm.refresh_field('custom_accepted_serial_nos');
                    frm.refresh_field('custom_rejected_serial_nos');
                    frm.refresh_field('custom_accepted_qty');
                    frm.refresh_field('custom_rejected_qty');
                    
                    frm.save();
                });

            }
        }
    });
 }
 
 // Handle bulk selection (Accept or Reject)
 function handle_bulk_selection(is_accept) {
    let selected_serials = $('.serial-checkbox:checked').map(function() {
        return $(this).data('serial');
    }).get();
 
    let all_serials = $('.serial-checkbox').map(function() {
        return $(this).data('serial');
    }).get();
 
    let non_selected_serials = all_serials.filter(serial => !selected_serials.includes(serial));
 
    let target_table = is_accept ? 'accepted-serials-table' : 'rejected-serials-table';
    let opposite_table = is_accept ? 'rejected-serials-table' : 'accepted-serials-table';
 
    move_bulk_serials_to_table(selected_serials, target_table);
    move_bulk_serials_to_table(non_selected_serials, opposite_table);
 }
 
 // Move a single serial number to a table
 function move_serial_to_table(serial, table_id) {
    let table_body = $('#' + table_id + ' tbody');
    
    // Remove "No Data" row if it exists
    if (table_body.find('tr td.text-center').length) {
        table_body.empty();
    }
    
    if (!table_body.find(`tr:contains('${serial}')`).length) {
        table_body.append(`<tr><td>${serial}</td></tr>`);
    }
 }
 
 // Remove a serial number from a table
 function remove_serial_from_table(serial, table_id) {
    let table_body = $('#' + table_id + ' tbody');
    
    table_body.find('tr').filter(function() {
        return $(this).find('td:first').text().trim() === serial;
    }).remove();
    
    // Add "No Data" row if table is empty
    if (!table_body.find('tr').length) {
        table_body.append('<tr><td class="text-center">No Data</td></tr>');
    }
 }
 
 // Move multiple serials to a table
 function move_bulk_serials_to_table(serials, table_id) {
    let table_body = $('#' + table_id + ' tbody');
    table_body.empty();
    
    if (!serials.length) {
        table_body.append('<tr><td class="text-center">No Data</td></tr>');
    } else {
        serials.forEach(serial => {
            table_body.append(`<tr><td>${serial}</td></tr>`);
        });
    }
 }
 
 // Get serial numbers from a table
 function get_serials_from_table(table_id) {
    return $('#' + table_id + ' tbody tr').map(function() {
        let cell_text = $(this).find('td:first').text().trim();
        return cell_text === 'No Data' ? null : cell_text;
    }).get().filter(Boolean);
 }
 
 // Update status badges in the main table
 function update_status_badges() {
    let accepted_serials = get_serials_from_table('accepted-serials-table');
    let rejected_serials = get_serials_from_table('rejected-serials-table');
    
    $('#all-serials-table tbody tr').each(function() {
        let serial = $(this).find('td:nth-child(2)').text();
        let status_badge = $(this).find('.status-badge');
        
        if (accepted_serials.includes(serial)) {
            status_badge.removeClass('badge-light badge-danger').addClass('badge-success');
            status_badge.text('Accepted');
        } else if (rejected_serials.includes(serial)) {
            status_badge.removeClass('badge-light badge-success').addClass('badge-danger');
            status_badge.text('Rejected');
        } else {
            status_badge.removeClass('badge-success badge-danger').addClass('badge-light');
            status_badge.text('Not Selected');
        }
    });
 }
 
 


