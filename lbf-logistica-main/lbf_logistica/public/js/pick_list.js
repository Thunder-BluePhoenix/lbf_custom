// frappe.ui.form.on('Pick List', {
//     refresh: function(frm) {
//         // Check if the locations table is empty
//         if (!frm.doc.locations || frm.doc.locations.length === 0) {
//             // If locations table is empty, add a row with the custom_item_code and custom_item_qty
//             frm.add_child('locations', {
//                 'item_code': frm.doc.custom_item_code,
//                 'qty': frm.doc.custom_item_qty,
//                 'stock_qty': frm.doc.custom_item_qty,
//                 'use_serial_batch_fields':1,
//                 'conversion_factor':1
//             });

//             // Refresh the locations table after adding the row
//             frm.refresh_field('locations');
//             frm.trigger('get_item_locations');
//             frm.set_value('status', "Draft");
//             frm.save();
//         }
//     }
// });

// frappe.ui.form.on('Pick List', {
//     refresh: function(frm) {
//         if (frm.doc.docstatus === 1) { // Button appears only after submission
//             frm.add_custom_button(__('Mark As Complete Via Stock Entry'), function() {
//                 frappe.call({
//                     method: 'lbf_logistica.overrides.pick_list.create_stock_entry',
//                     args: {
//                         pick_list_name: frm.doc.name
//                     },
//                     callback: function(response) {
//                         if (response.message) {
//                             // frappe.msgprint(__('Stock Entry created: ' + response.message));
//                             frappe.set_route('Form', 'Stock Entry', response.message); // Redirect to Stock Entry
//                         }
//                     }
//                 });
//             }, __('Create'));
//         }
//     }
// });

frappe.ui.form.on('Pick List', {
    refresh: function(frm) {
        frm.set_query('custom_loading_zone', function () {
            return {
                filters: {
                    custom_type_of_warehouse: ['in', ['Loading Zone', 'Both Loading and Un-Loading Zone']]
                }
            };
        });
        if (frm.doc.docstatus === 1) { // Button appears only after submission
            frm.add_custom_button(__('Mark As Complete Via Stock Entry'), function() {
                // Get the default loading warehouse from the custom_loading_zone field in Pick List
                const default_loading_warehouse = frm.doc.custom_loading_zone || '';
 
                // Initialize the items for the dialog
                const items = frm.doc.custom_item_locations.map(loc => ({
                    item_code: loc.item_code,
                    source_warehouse: loc.location || '',
                    target_warehouse: loc.target_warehouse || default_loading_warehouse,
                    qty: loc.qty,
                    serial_no: loc.serial_no || '',
                    batch_no: loc.batch_no || '',
                    idx: loc.idx // To update the correct child table row later
                }));
 
                // Show the dialog
                const d = new frappe.ui.Dialog({
                    title: __('Update Target Warehouse'),
                    fields: [
                        {
                            fieldname: 'custom_item_locations',
                            fieldtype: 'Table',
                            label: __('Pick List Items'),
                            cannot_add_rows: true,
                            in_place_edit: true,
                            fields: [
                                { fieldtype: 'Data', fieldname: 'item_code', label: 'Item Code', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Link', fieldname: 'source_warehouse', label: 'Source Warehouse', options: 'Warehouse', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Link', fieldname: 'target_warehouse', label: 'Target Warehouse', options: 'Warehouse', in_list_view: 1, 
                                    get_query: () => {
                                        return {
                                            filters: [
                                                ["Warehouse", "custom_type_of_warehouse", "in", ["Loading Zone", "Both Loading and Un-Loading Zone"]]
                                            ]
                                        };
                                    }
                                
                                },
                                { fieldtype: 'Float', fieldname: 'qty', label: 'Qty', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Link', fieldname: 'serial_no', label: 'Serial No', options: 'Serial No', in_list_view: 1, read_only: 1 },
                                { fieldtype: 'Link', fieldname: 'batch_no', label: 'Batch No', options: 'Batch', in_list_view: 1, read_only: 1 }
                            ]
                        }
                    ],
                    primary_action_label: __('Proceed'),
                    size: 'large',
                    primary_action: function(values) {
                        // Update the target_warehouse in the child table
                        values.custom_item_locations.forEach(item => {
                            const row = frm.doc.custom_item_locations.find(loc => loc.idx === item.idx);
                            if (row) {
                                row.target_warehouse = item.target_warehouse;
                            }
                        });
 
                        // Refresh the form to reflect updates
                        frm.refresh_field('custom_item_locations');
 
                        // Proceed to create Stock Entry
                        frappe.call({
                            method: 'lbf_logistica.overrides.pick_list.create_stock_entry',
                            args: {
                                pick_list_name: frm.doc.name,
                                dialog_data: values.custom_item_locations
                            },
                            callback: function(response) {
                                if (response.message) {
                                    frappe.set_route('Form', 'Stock Entry', response.message); // Redirect to Stock Entry
                                }
                            }
                        });
 
                        d.hide();
                    }
                });
 
                // Set data and show the dialog
                d.fields_dict.custom_item_locations.df.data = items;
                d.fields_dict.custom_item_locations.grid.refresh();
                d.show();
            }, __('Create'));
        }
        setTimeout(function() {
            // if (frm.doc.docstatus === 1) {  // Check if the Sales Order is submitted
                // Hide the buttons by their labels
                frm.remove_custom_button('Update Current Stock');
                frm.remove_custom_button('Stock Entry', 'Create');
               
                
        }, 300); 
        const status_colors = {
            "Open": "orange",
            "In Progress": "blue",
            "Completed": "green",
            "Cancelled": "red"
        };

        const color = status_colors[frm.doc.custom_pl_status] || "gray";

        // Create a custom status bar
        if (frm.doc.custom_pl_status) {
            frm.page.set_indicator(
                `${frm.doc.custom_pl_status}`, // Status text
                color // Color
            );
        }
        if (frm.doc.custom_whole_items_details) {
            let details = frm.doc.custom_whole_items_details.split("\n");
            let batchData = {};

            details.forEach(detail => {
                let match = detail.match(/Item Code: (.*?), Item Name: (.*?), Serial No: (.*?), Batch No: (.*?), Location: (.*?), Target Warehouse: (.*)/);
                
                if (match) {
                    let item_code = match[1];
                    let item_name = match[2];
                    let batch_no = match[4];
                    let location = match[5];

                    let key = `${batch_no}_${location}`;

                    if (!batchData[key]) {
                        batchData[key] = {
                            batch_no: batch_no,
                            location: location,
                            item_name: item_name,
                            qty: 0
                        };
                    }

                    batchData[key].qty += 1;
                }
            });

            let table_html = `
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Batch ID</th>
                            <th>Location</th>
                            <th>Item Name</th>
                            <th>Quantity</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            Object.values(batchData).forEach(row => {
                table_html += `
                    <tr>
                        <td>${row.batch_no}</td>
                        <td>${row.location}</td>
                        <td>${row.item_name}</td>
                        <td>${row.qty}</td>
                    </tr>
                `;
            });

            table_html += `</tbody></table>`;

            frm.set_df_property('custom_batch_details_html', 'options', table_html);
            frm.refresh_field('custom_batch_details_html');
        }
    }
 });
 
 
 











 frappe.ui.form.on('Pick List', {
    refresh: function(frm) {
        if(frm.doc.docstatus === 0){
            frm.add_custom_button(__('Scan'), function() {
                open_scan_dialog(frm);
            });
            frm.add_custom_button(__('Bulk Select'), function() {
                open_bulk_select_dialog(frm);
            });
        }
    }
});

function open_bulk_select_dialog(frm) {
    let item_code = frm.doc.custom_item_code;
    let item_name = frm.doc.custom_item_name;
    let item_qty = frm.doc.custom_item_qty || 0;
    let loading_zone = frm.doc.custom_loading_zone;
    let tyre_type = frm.doc.custom_item_type;

    if (!item_code) {
        frappe.msgprint(__('Item Code is required.'));
        return;
    }

    // Parse serial numbers from the long text field
    let serials = parse_serial_numbers(frm.doc.custom_whole_items_details);
    
    // Get existing serial numbers from child table
    let existing_serials = frm.doc.custom_item_locations || [];
    let existing_serial_nos = existing_serials.map(row => row.serial_no);
    let selected_count = existing_serial_nos.length; // Initialize with existing count

    let dialog = new frappe.ui.Dialog({
        title: 'Bulk Select Items',
        size: 'extra-large',
        fields: [
            { fieldname: 'item_code', label: 'Item Code', fieldtype: 'Data', default: item_code, read_only: 1 },
            { fieldname: 'loading_zone', label: 'Loading Zone', fieldtype: 'Link', options: 'Warehouse', default: loading_zone,
                get_query: () => {
                    return {
                        filters: [
                            ["Warehouse", "custom_type_of_warehouse", "in", ["Loading Zone", "Both Loading and Un-Loading Zone"]]
                        ]
                    };
                }
            },
            { fieldtype: 'Column Break' },
            { fieldname: 'item_name', label: 'Item Name', fieldtype: 'Data', default: item_name, read_only: 1 },
            { fieldname: 'tyre_type', label: 'Tyre Type', fieldtype: 'Data', default: tyre_type, read_only: 1 },
            { fieldtype: 'Column Break' },
            { fieldname: 'item_qty', label: 'Item Quantity', fieldtype: 'Int', default: item_qty, read_only: 1 },
            { fieldtype: 'Section Break' },
            { fieldname: 'serial_filter', label: 'Filter by Serial No', fieldtype: 'Data' },
            { fieldtype: 'Column Break' },
            { fieldname: 'batch_filter', label: 'Filter by Batch No', fieldtype: 'Data' },
            { fieldtype: 'Section Break' },
            { fieldname: 'serial_numbers_html', fieldtype: 'HTML' }
        ],
        primary_action_label: __('Proceed (' + selected_count + '/' + item_qty + ')'),
        primary_action: function(data) {
            let selected_serials = get_selected_serials();
            if (selected_serials.length === 0) {
                frappe.msgprint(__('Please select at least one serial number.'));
                return;
            }
            if (selected_serials.length > item_qty) {
                frappe.msgprint(__('You cannot select MORE than {0} serial numbers.', [item_qty]));
                return;
            }

            update_selected_serials(frm, selected_serials, data.loading_zone);
            dialog.hide();
            frm.save();
        }
    });

    dialog.show();

    // Generate and insert the HTML table with pre-checked serials
    let table_html = `
        <div class="selected-count mb-3">Selected: <span id="selected_count">${selected_count}</span> / ${item_qty}</div>
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th style="width: 5%;"><input type="checkbox" id="select_all"></th>
                    <th>Serial No</th>
                    <th>Batch No</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody id="serial_table_body">
                ${serials.map(sr => `
                    <tr>
                        <td><input type="checkbox" class="serial-checkbox" 
                            data-serial="${sr.serial_no}" 
                            data-batch="${sr.batch_no}" 
                            data-location="${sr.location}"
                            ${existing_serial_nos.includes(sr.serial_no) ? 'checked' : ''}>
                        </td>
                        <td>${sr.serial_no}</td>
                        <td>${sr.batch_no}</td>
                        <td>${sr.location}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    dialog.fields_dict.serial_numbers_html.$wrapper.html(table_html);

    // Handle checkbox selection and validation
    let checkboxes = dialog.fields_dict.serial_numbers_html.$wrapper.find('.serial-checkbox');
    let proceed_button = dialog.get_primary_btn();

    function updateSelectedCount() {
        selected_count = checkboxes.filter(':checked').length;
        $('#selected_count').text(selected_count);
        proceed_button.prop('disabled', selected_count > item_qty);
        dialog.set_primary_action(__('Proceed (' + selected_count + '/' + item_qty + ')'));
    }

    // Initialize selected count for pre-checked boxes
    updateSelectedCount();
    
    checkboxes.on('change', updateSelectedCount);

    // Filter functionality
    function applyFilters() {
        let serialFilter = dialog.get_value('serial_filter').toLowerCase();
        let batchFilter = dialog.get_value('batch_filter').toLowerCase();

        $('#serial_table_body tr').each(function() {
            let row = $(this);
            let serialNo = row.find('td:eq(1)').text().toLowerCase();
            let batchNo = row.find('td:eq(2)').text().toLowerCase();
            
            let serialMatch = !serialFilter || serialNo.includes(serialFilter);
            let batchMatch = !batchFilter || batchNo.includes(batchFilter);
            
            row.toggle(serialMatch && batchMatch);
        });
    }

    dialog.fields_dict.serial_filter.$input.on('input', applyFilters);
    dialog.fields_dict.batch_filter.$input.on('input', applyFilters);

    dialog.fields_dict.serial_numbers_html.$wrapper.find('#select_all').on('change', function() {
        let checked = $(this).prop('checked');
        checkboxes.filter(':visible').prop('checked', checked).trigger('change');
        updateSelectedCount();
    });
}

function open_scan_dialog(frm) {
    let item_code = frm.doc.custom_item_code;
    let item_name = frm.doc.custom_item_name;
    let item_qty = frm.doc.custom_item_qty || 0;
    let loading_zone = frm.doc.custom_loading_zone;
    let tyre_type = frm.doc.custom_item_type;

    if (!item_code) {
        frappe.msgprint(__('Item Code is required.'));
        return;
    }

    // Parse serial numbers from the long text field for validation
    let available_serials = parse_serial_numbers(frm.doc.custom_whole_items_details);
    
    // Get existing scanned serials from child table
    let existing_serials = frm.doc.custom_item_locations || [];
    let scanned_serials = existing_serials.map(row => ({
        serial_no: row.serial_no,
        batch_no: row.batch_no,
        location: row.location
    }));

    let dialog = new frappe.ui.Dialog({
        title: 'Scan Items',
        size: 'extra-large',
        fields: [
            { fieldname: 'item_code', label: 'Item Code', fieldtype: 'Data', default: item_code, read_only: 1 },
            { fieldname: 'loading_zone', label: 'Loading Zone', fieldtype: 'Link', options: 'Warehouse', default: loading_zone,
                get_query: () => {
                    return {
                        filters: [
                            ["Warehouse", "custom_type_of_warehouse", "in", ["Loading Zone", "Both Loading and Un-Loading Zone"]]
                        ]
                    };
                }
            },
            { fieldtype: 'Column Break' },
            { fieldname: 'item_name', label: 'Item Name', fieldtype: 'Data', default: item_name, read_only: 1 },
            { fieldname: 'tyre_type', label: 'Tyre Type', fieldtype: 'Data', default: tyre_type, read_only: 1 },
            { fieldtype: 'Column Break' },
            { fieldname: 'item_qty', label: 'Item Quantity', fieldtype: 'Int', default: item_qty, read_only: 1 },
            { fieldtype: 'Section Break' },
            { fieldname: 'available_serials_html', fieldtype: 'HTML', label: 'Available Items' },
            { fieldtype: 'Column Break' },
            { fieldname: 'barcode_section', fieldtype: 'HTML', label: 'Scan Barcode' }
        ],
        primary_action_label: __('Proceed (' + scanned_serials.length + '/' + item_qty + ')'),
        primary_action: function(data) {
            if (scanned_serials.length === 0) {
                frappe.msgprint(__('Please scan at least one serial number.'));
                return;
            }
            if (scanned_serials.length > item_qty) {
                frappe.msgprint(__('You cannot scan MORE than {0} serial numbers.', [item_qty]));
                return;
            }

            update_selected_serials(frm, scanned_serials, data.loading_zone);
            dialog.hide();
            frm.save();
        }
    });

    dialog.show();

    // Generate and insert the Available Items HTML table
    let available_items_html = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Serial No</th>
                    <th>Batch No</th>
                </tr>
            </thead>
            <tbody>
                ${available_serials.map(sr => `
                    <tr>
                        <td>${sr.serial_no}</td>
                        <td>${sr.batch_no}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    dialog.fields_dict.available_serials_html.$wrapper.html(available_items_html);

    // Generate and insert the Barcode Scanner section with pre-populated scanned items
    let barcode_section_html = `
        <div class="barcode-section">
            <div class="input-group">
                <input type="text" class="form-control barcode-input" placeholder="Scan or enter barcode">
                <div class="input-group-append">
                    <button class="btn btn-default scan-button">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                            <circle cx="12" cy="13" r="4"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="mt-4">
                <div class="table-responsive" style="overflow-x: auto; -webkit-overflow-scrolling: touch; max-width: 100%;">
                    <table class="table table-bordered" style="min-width: 300px;">
                        <thead>
                            <tr>
                                <th style="width: 30px;">ID</th>
                                <th style="min-width: 120px;">Serial No</th>
                                <th style="min-width: 120px;">Batch No</th>
                            </tr>
                        </thead>
                        <tbody class="scanned-items-body">
                            ${scanned_serials.map(sr => `
                                <tr>
                                    <td style="width: 30px;">
                                        <input type="checkbox" class="scanned-checkbox" checked 
                                            data-serial="${sr.serial_no}" 
                                            data-batch="${sr.batch_no}"
                                            data-location="${sr.location}">
                                    </td>
                                    <td>${sr.serial_no}</td>
                                    <td>${sr.batch_no}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    dialog.fields_dict.barcode_section.$wrapper.html(barcode_section_html);

    // Update scanned serials when checkboxes change
    function updateScannedSerials() {
        scanned_serials = [];
        dialog.fields_dict.barcode_section.$wrapper.find('.scanned-checkbox:checked').each(function() {
            scanned_serials.push({
                serial_no: $(this).data('serial'),
                batch_no: $(this).data('batch'),
                location: $(this).data('location')
            });
        });
        dialog.set_primary_action(__('Proceed (' + scanned_serials.length + '/' + item_qty + ')'));
    }

    dialog.fields_dict.barcode_section.$wrapper.on('change', '.scanned-checkbox', updateScannedSerials);

    // Rest of the scanning functionality
    let $barcodeInput = dialog.fields_dict.barcode_section.$wrapper.find('.barcode-input');
    let $scanButton = dialog.fields_dict.barcode_section.$wrapper.find('.scan-button');

    function processBarcodeInput(barcode) {
        if (!barcode) return;

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Serial No',
                filters: {
                    'custom_barcode': barcode
                },
                fields: ['name', 'batch_no']
            },
            callback: function(response) {
                if (response.message && response.message.length > 0) {
                    let serial_doc = response.message[0];

                    // Check for duplicate scan
                    if (scanned_serials.some(sr => sr.serial_no === serial_doc.name)) {
                        frappe.msgprint(__('This serial number has already been scanned.'));
                        initializeCamera();
                        return;
                    }

                    // Check if batch exists in available serials
                    let batch_exists = available_serials.some(sr =>
                        sr.serial_no === serial_doc.name && sr.batch_no === serial_doc.batch_no
                    );

                    if (!batch_exists) {
                        frappe.msgprint(__('Invalid batch number or serial number.'));
                        initializeCamera();
                        return;
                    }

                    // Add to scanned serials
                    let serial_info = {
                        serial_no: serial_doc.name,
                        batch_no: serial_doc.batch_no,
                        location: available_serials.find(sr => sr.serial_no === serial_doc.name)?.location || ''
                    };

                    scanned_serials.push(serial_info);

                    // Update scanned items table
                    let $scannedBody = dialog.fields_dict.barcode_section.$wrapper.find('.scanned-items-body');
                    $scannedBody.append(`
                        <tr>
                            <td>
                                <input type="checkbox" class="scanned-checkbox" checked 
                                    data-serial="${serial_info.serial_no}" 
                                    data-batch="${serial_info.batch_no}"
                                    data-location="${serial_info.location}">
                            </td>
                            <td>${serial_info.serial_no}</td>
                            <td>${serial_info.batch_no}</td>
                        </tr>
                    `);

                    // Update proceed button
                    dialog.set_primary_action(__('Proceed (' + scanned_serials.length + '/' + item_qty + ')'));

                    // Clear input and continue scanning
                    $barcodeInput.val('');
                    initializeCamera();
                } else {
                    frappe.msgprint(__('Invalid barcode.'));
                    initializeCamera();
                }
            }
        });
    }

    function initializeCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            frappe.msgprint(__('Camera access is not supported in this browser.'));
            return;
        }

        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
            .then(function(stream) {
                let $scannerWrapper = dialog.fields_dict.barcode_section.$wrapper;
                // Remove existing scanner UI if any
                $scannerWrapper.find('.camera-container').remove();

                // Create a smaller scanner module inside the dialog
                let scannerHtml = `
                    <div class="camera-container" style="position: relative; text-align: center; margin-top: 10px;">
                        <video id="barcode-video" autoplay playsinline
                            style="width: 100%; max-height: 150px; border: 2px solid #ddd; border-radius: 8px;">
                        </video>
                        <button id="close-camera" class="btn btn-danger btn-sm"
                            style="position: absolute; top: 5px; right: 5px;">
                            ×
                        </button>
                    </div>
                `;
                $scannerWrapper.append(scannerHtml);

                let video = document.getElementById("barcode-video");
                video.srcObject = stream;

                let closeButton = document.getElementById("close-camera");
                closeButton.onclick = function() {
                    stream.getTracks().forEach(track => track.stop());
                    $scannerWrapper.find('.camera-container').remove();
                };

                let canvas = document.createElement('canvas');
                let context = canvas.getContext('2d');

                if ('BarcodeDetector' in window) {
                    let barcodeDetector = new BarcodeDetector();

                    function detectBarcode() {
                        if ($scannerWrapper.find('.camera-container').length > 0) {
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                            context.drawImage(video, 0, 0, canvas.width, canvas.height);

                            barcodeDetector.detect(canvas)
                                .then(barcodes => {
                                    if (barcodes.length > 0) {
                                        stream.getTracks().forEach(track => track.stop());
                                        $scannerWrapper.find('.camera-container').remove();
                                        processBarcodeInput(barcodes[0].rawValue);
                                    } else {
                                        requestAnimationFrame(detectBarcode);
                                    }
                                })
                                .catch(err => {
                                    console.error(err);
                                    requestAnimationFrame(detectBarcode);
                                });
                        }
                    }
                    detectBarcode();
                } else {
                    frappe.msgprint(__('Barcode detection is not supported in this browser.'));
                    stream.getTracks().forEach(track => track.stop());
                    $scannerWrapper.find('.camera-container').remove();
                }
            })
            .catch(function(error) {
                frappe.msgprint(__('Error accessing camera: ') + error.message);
            });
    }

    $barcodeInput.on('keypress', function(e) {
        if (e.which === 13) {
            processBarcodeInput($(this).val());
        }
    });

    $scanButton.on('click', function() {
        initializeCamera();
    });
}

// Helper functions
function get_selected_serials() {
    let selected = [];
    $('#serial_table_body .serial-checkbox:checked').each(function() {
        selected.push({
            serial_no: $(this).data('serial'),
            batch_no: $(this).data('batch'),
            location: $(this).data('location')
        });
    });
    return selected;
}

function parse_serial_numbers(text_data) {
    if (!text_data) return [];
    let lines = text_data.split("\n");
    let serials = [];
    lines.forEach(line => {
        let parts = line.match(/Item Code: (.*?), Item Name: (.*?), Serial No: (.*?), Batch No: (.*?), Location: (.*?), Target Warehouse: (.*)/);
        if (parts) {
            serials.push({
                serial_no: parts[3],
                batch_no: parts[4],
                location: parts[5]
            });
        }
    });
    return serials;
}

function update_selected_serials(frm, selected_serials, loading_zone) {
    frm.clear_table('custom_item_locations');
    selected_serials.forEach(row => {
        let new_row = frm.add_child('custom_item_locations');
        if (new_row) {
            new_row.item_code = frm.doc.custom_item_code;
            new_row.item_name = frm.doc.custom_item_name;
            new_row.serial_no = row.serial_no;
            new_row.batch_no = row.batch_no;
            new_row.location = row.location;
            new_row.target_warehouse = loading_zone;
            new_row.qty = 1;
        }
    });
    frm.set_value('custom_loading_zone', loading_zone);
    frm.refresh_field('custom_item_locations');
    frm.refresh_field('custom_loading_zone');
}


 
 
 
 
 





















 


// frappe.ui.form.on('Pick List', {
//     refresh: function (frm) {
//         setTimeout(function() {
//             // if (frm.doc.docstatus === 1) {  // Check if the Sales Order is submitted
//                 // Hide the buttons by their labels
//                 frm.remove_custom_button('Update Current Stock');
//                 frm.remove_custom_button('Stock Entry', 'Create');
               
                
//         }, 300); 
//     }
//  });
 

//  frappe.ui.form.on('Pick List', {
//     refresh: function (frm) {
//         // Remove default workflow status bar
//         // frm.page.remove_inner_button('Workflow', 'status');

//         // Map `custom_pl_status` to color indicators
//         const status_colors = {
//             "Open": "orange",
//             "In Progress": "blue",
//             "Completed": "green",
//             "Cancelled": "red"
//         };

//         const color = status_colors[frm.doc.custom_pl_status] || "gray";

//         // Create a custom status bar
//         if (frm.doc.custom_pl_status) {
//             frm.page.set_indicator(
//                 `${frm.doc.custom_pl_status}`, // Status text
//                 color // Color
//             );
//         }
//     },
// });


// frappe.ui.form.on('Pick List', {
//     refresh: function(frm) {
//         if (frm.doc.custom_whole_items_details) {
//             let details = frm.doc.custom_whole_items_details.split("\n");
//             let batchData = {};

//             details.forEach(detail => {
//                 let match = detail.match(/Item Code: (.*?), Item Name: (.*?), Serial No: (.*?), Batch No: (.*?), Location: (.*?), Target Warehouse: (.*)/);
                
//                 if (match) {
//                     let item_code = match[1];
//                     let item_name = match[2];
//                     let batch_no = match[4];
//                     let location = match[5];

//                     let key = `${batch_no}_${location}`;

//                     if (!batchData[key]) {
//                         batchData[key] = {
//                             batch_no: batch_no,
//                             location: location,
//                             item_name: item_name,
//                             qty: 0
//                         };
//                     }

//                     batchData[key].qty += 1;
//                 }
//             });

//             let table_html = `
//                 <table class="table table-bordered">
//                     <thead>
//                         <tr>
//                             <th>Batch ID</th>
//                             <th>Location</th>
//                             <th>Item Name</th>
//                             <th>Quantity</th>
//                         </tr>
//                     </thead>
//                     <tbody>
//             `;

//             Object.values(batchData).forEach(row => {
//                 table_html += `
//                     <tr>
//                         <td>${row.batch_no}</td>
//                         <td>${row.location}</td>
//                         <td>${row.item_name}</td>
//                         <td>${row.qty}</td>
//                     </tr>
//                 `;
//             });

//             table_html += `</tbody></table>`;

//             frm.set_df_property('custom_batch_details_html', 'options', table_html);
//             frm.refresh_field('custom_batch_details_html');
//         }
//     }
// });


