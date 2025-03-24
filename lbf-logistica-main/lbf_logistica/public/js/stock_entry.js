frappe.ui.form.on('Stock Entry', {
    custom_barcode_scanner: function(frm) {
        let barcode = frm.doc.custom_barcode_scanner;
        
        if (barcode) {
            let duplicate = frm.doc.items.some(item => item.custom_barcode_of_serial === barcode);
            
            if (duplicate) {
                frappe.msgprint({
                    title: __('Duplicate Barcode'),
                    message: __('This barcode has already been scanned.'),
                    indicator: 'red'
                });
                
                // Clear the barcode scanner field
                frm.set_value('custom_barcode_scanner', '');
                return;
            }

            frappe.flags.hide_serial_batch_dialog = true;
            frappe.call({
                method: 'lbf_logistica.overrides.stock_entry_scan_barcode.scan_serial_no_barcode',
                args: {
                    barcode: barcode,
                    stock_entry_doc: frm.doc
                },
                callback: function(response) {
                    if (response.message) {
                        let item_details = response.message;
                        
                        // Add new row to items table
                        let new_row = frm.add_child('items');
                        frappe.model.set_value(new_row.doctype, new_row.name, 'item_code', item_details.item_code);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'custom_serial_noo', item_details.serial_no);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'serial_no', item_details.serial_no);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'custom_batch_id', item_details.batch);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'batch_no', item_details.batch);
                        frappe.model.set_value(new_row.doctype, new_row.name, 's_warehouse', item_details.from_warehouse);                      
                        frappe.model.set_value(new_row.doctype, new_row.name, 'use_serial_batch_fields', 1);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'transferred_qty', item_details.qty);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'qty', item_details.qty);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'actual_qty', item_details.actual_qty);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'uom', item_details.uom);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'basic_rate', 0);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'valuation_rate', 0);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'custom_scanned', 1);
                        frappe.model.set_value(new_row.doctype, new_row.name, 'custom_barcode_of_serial', barcode);
                        
                        // Clear the barcode scanner fieldactual_qtyuomuse_serial_batch_field.has_item_scanned.actual_qtyvaluation_rate
                        frm.set_value('custom_barcode_scanner', '');
                        
                        // Refresh the form
                        frm.refresh_field('items');
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Stock Entry', {
    onload: function(frm) {
        if (frm.is_new()) {
            
            frm.clear_table('items');
            frm.refresh_field('items');
        }
    },
})


// frappe.require("https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js", function() {
    frappe.ui.form.on('Stock Entry', {
        refresh: function (frm) {
            // Add barcode scanner icon to the custom_barcode_scanner field
            let $fieldWrapper = frm.fields_dict['custom_barcode_scanner'].$wrapper;
            $fieldWrapper.addClass('has-scanner-icon');
    
            // Create scanner icon with updated CSS
            let $scanIcon = $(`
                <span style="
                    position: absolute;
                    right: 5px;
                    top: 50%;
                    transform: translateY(-50%);
                    cursor: pointer;
                    z-index: 10;
                    color: #5e64ff;
                    opacity: 0.7;
                    transition: opacity 0.3s ease;
                " class="barcode-scanner-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                         fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                         style="display: block;">
                        <path d="M4 7V4a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v3"/>
                        <path d="M5 20a2 2 0 0 1-2-2v-5h18v5a2 2 0 0 1-2 2Z"/>
                        <path d="M16 8v-4H8v4"/>
                    </svg>
                </span>
            `);
    
            // Style the input field to accommodate the icon
            $fieldWrapper.find('input').css({
                'padding-right': '30px', // Make space for the icon
                'box-sizing': 'border-box'
            });
    
            // Position the field wrapper
            $fieldWrapper.css({
                'position': 'relative'
            });
    
            // Remove any existing scanner icon first
            $fieldWrapper.find('.barcode-scanner-icon').remove();
    
            // Append the new scanner icon
            $fieldWrapper.find('.control-input').append($scanIcon);
    
            // Add hover effect
            $scanIcon.on('mouseenter', function () {
                $(this).css('opacity', '1');
            }).on('mouseleave', function () {
                $(this).css('opacity', '0.7');
            });
    
            // Add click event to scanner icon
            $scanIcon.on('click', function () {
                startBarcodeScanning(frm);
            });

            setTimeout(function () {
                frm.remove_custom_button('Material Request', 'Create');
                frm.remove_custom_button('Material Request', 'Get Items From');
                frm.remove_custom_button('Purchase Invoice', 'Get Items From');
                frm.remove_custom_button('Bill of Materials', 'Get Items From');
                frm.remove_custom_button('Transit Entry', 'Get Items From');
                
            }, 300);

            
        },
    
    
        custom_barcode_scanner: function (frm) {
            let barcode = frm.doc.custom_barcode_scanner;
    
            if (barcode) {
                let duplicate = frm.doc.items.some(item => item.custom_barcode_of_serial === barcode);
    
                if (duplicate) {
                    frappe.msgprint({
                        title: __('Duplicate Barcode'),
                        message: __('This barcode has already been scanned.'),
                        indicator: 'red'
                    });
    
                    // Clear the barcode scanner field
                    frm.set_value('custom_barcode_scanner', '');
                    return;
                }
    
                frappe.flags.hide_serial_batch_dialog = true;
                frappe.call({
                    method: 'lbf_logistica.overrides.stock_entry_scan_barcode.scan_serial_no_barcode',
                    args: {
                        barcode: barcode,
                        stock_entry_doc: frm.doc
                    },
                    callback: function (response) {
                        if (response.message) {
                            let item_details = response.message;
    
                            // Add new row to items table
                            let new_row = frm.add_child('items');
                            frappe.model.set_value(new_row.doctype, new_row.name, 'item_code', item_details.item_code);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_serial_noo', item_details.serial_no);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'serial_no', item_details.serial_no);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_batch_id', item_details.batch);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'batch_no', item_details.batch);
                            frappe.model.set_value(new_row.doctype, new_row.name, 's_warehouse', item_details.from_warehouse);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'use_serial_batch_fields', 1);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'transferred_qty', item_details.qty);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'qty', item_details.qty);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'actual_qty', item_details.actual_qty);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'uom', item_details.uom);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'basic_rate', 0);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'valuation_rate', 0);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_scanned', 1);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_barcode_of_serial', barcode);
    
                            // Clear the barcode scanner field
                            frm.set_value('custom_barcode_scanner', '');
    
                            // Refresh the form
                            frm.refresh_field('items');
                        }
                    }
                });
            }
        }
    });
    
    // Barcode scanning function using BarcodeDetector API
    async function startBarcodeScanning(frm) {
        if (!('BarcodeDetector' in window)) {
            frappe.msgprint(__('Barcode scanning is not supported in this browser.'));
            return;
        }
    
        const barcodeDetector = new BarcodeDetector({ formats: ['code_128', 'ean_13'] });
    
        // Stop any existing video streams
        if (window.scannerStream) {
            window.scannerStream.getTracks().forEach(track => track.stop());
            window.scannerStream = null;
        }
    
        // Remove existing video element if present to prevent reuse issues
        const existingVideo = document.getElementById('video-scanner');
        if (existingVideo) {
            existingVideo.remove();
        }
    
        // Initialize scanner modal
        let scannerModal = new frappe.ui.Dialog({
            title: 'Scan Barcode',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'scanner_container',
                    options: `
                        <div style="width:100%; height:400px;">
                            <video id="video-scanner" style="width:100%; height:100%; object-fit:cover;"></video>
                        </div>
                    `
                }
            ],
            primary_action_label: 'Close Scanner',
            primary_action: function () {
                if (window.scannerStream) {
                    window.scannerStream.getTracks().forEach(track => track.stop());
                    window.scannerStream = null;
                }
                scannerModal.hide();
            }
        });
    
        scannerModal.show();
    
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            window.scannerStream = stream;
    
            // Wait for the modal to fully render before accessing the video element
            setTimeout(() => {
                const video = document.getElementById('video-scanner');
                if (!video) {
                    frappe.msgprint(__('Video element not found. Please try again.'));
                    scannerModal.hide();
                    return;
                }
    
                video.srcObject = stream;
                video.setAttribute('playsinline', true);
                video.play();
    
                const detectBarcode = async () => {
                    if (video.readyState === video.HAVE_ENOUGH_DATA) {
                        const barcodes = await barcodeDetector.detect(video);
                        if (barcodes.length > 0) {
                            frm.set_value('custom_barcode_scanner', barcodes[0].rawValue);
    
                            // Stop the video stream and close the modal
                            window.scannerStream.getTracks().forEach(track => track.stop());
                            window.scannerStream = null;
                            scannerModal.hide();
                        } else {
                            requestAnimationFrame(detectBarcode);
                        }
                    } else {
                        requestAnimationFrame(detectBarcode);
                    }
                };
    
                detectBarcode();
            }, 200); // Short delay to ensure video element is rendered
        } catch (err) {
            frappe.msgprint(__('Error accessing camera: ') + err.message);
    
            // Ensure stream is stopped if an error occurs
            if (window.scannerStream) {
                window.scannerStream.getTracks().forEach(track => track.stop());
                window.scannerStream = null;
            }
            scannerModal.hide();
        }
    }
    
    
    
    
    
    // });
    
    

    frappe.ui.form.on('Stock Entry', {
        custom_serial_and_batch_bundle_id: function(frm) {
            let bundle_id = frm.doc.custom_serial_and_batch_bundle_id;
            
            if (!bundle_id) return;
            
            // Prevent duplicate bundles
            let existing_bundle = frm.doc.items.some(item => 
                item.custom_serial_and_batch_bundle_id === bundle_id
            );
            
            if (existing_bundle) {
                frappe.msgprint({
                    title: __('Duplicate Bundle'),
                    message: __('This Serial and Batch Bundle has already been added.'),
                    indicator: 'red'
                });
                frm.set_value('custom_serial_and_batch_bundle_id', '');
                return;
            }
            frappe.flags.hide_serial_batch_dialog = true;
            frappe.call({
                method: 'lbf_logistica.overrides.stock_entry_scan_barcode.populate_stock_entry_from_bundle',
                args: {
                    bundle_id: bundle_id,
                    stock_entry_doc: frm.doc
                },
                callback: function(response) {
                    if (response.message && response.message.length > 0) {
                        // Process each item in the bundle
                        response.message.forEach(function(item_details) {
                            // Add new row to items table
                            let new_row = frm.add_child('items');
                            
                            // Set values for the new row
                            frappe.model.set_value(new_row.doctype, new_row.name, 'item_code', item_details.item_code);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_serial_noo', item_details.serial_no);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'serial_no', item_details.serial_no);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_batch_id', item_details.batch);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'batch_no', item_details.batch);
                            frappe.model.set_value(new_row.doctype, new_row.name, 's_warehouse', item_details.from_warehouse);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'use_serial_batch_fields', 1);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'transferred_qty', item_details.qty);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'qty', item_details.qty);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'actual_qty', item_details.actual_qty);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'uom', item_details.uom);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'basic_rate', 0);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'valuation_rate', 0);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_scanned', 0);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_through_serial_and_batch_bundle', 1);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_serial_and_batch_bundle_id', item_details.custom_serial_and_batch_bundle_id);
                            frappe.model.set_value(new_row.doctype, new_row.name, 'custom_barcode_of_serial', item_details.barcode);
                        });
                        
                        // Clear the bundle ID fieldcustom_through_serial_and_batch_bundle.barcode
                        frm.set_value('custom_serial_and_batch_bundle_id', '');
                        
                        // Refresh the form
                        frm.refresh_field('items');
                    } else {
                        frappe.msgprint({
                            title: __('No Items'),
                            message: __('No items found in the selected Serial and Batch Bundle.'),
                            indicator: 'yellow'
                        });
                    }
                }
            });
        }
    });
    
    

 

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        frm.add_custom_button(('Allocate Location For Selected Items'), () => {
            let selected_items = frm.fields_dict["items"].grid.get_selected_children();
           
            if (!selected_items.length) {
                frappe.msgprint('Please select at least one item.');
                return;
            }
 
 
            // Debug log for selected rows
            selected_items.forEach(row => {
                console.log("Row data:", row);
            });
 
 
            try {
                let serial_nos = selected_items.map(row => {
                    if (!row.custom_serial_noo) {
                        console.log("Missing serial number for row:", row);
                        return '';
                    }
                    return row.custom_serial_noo;
                }).filter(Boolean).join(', ');
 
 
                let d = new frappe.ui.Dialog({
                    title: ('Allocate Location'),
                    fields: [
                        {
                            label: ('Serial Nos'),
                            fieldname: 'serial_nos',
                            fieldtype: 'Small Text',
                            read_only: 1,
                            default: serial_nos
                        },
                        {
                            label: ('Target Warehouse'),
                            fieldname: 'target_warehouse',
                            fieldtype: 'Link',
                            options: 'Warehouse',
                            reqd: 1,
                            get_query: () => {
                                return {
                                    filters: [["Warehouse", "custom_type_of_warehouse", "=", "Location"]]
                                };
                            }
                        },
                
                        
                    ],
                    primary_action_label: ('Proceed'),
                    primary_action(values) {
                        // Check for existing warehouses
                        let rows_with_warehouse = selected_items.filter(row => row.t_warehouse);
                       
                        if (rows_with_warehouse.length) {
                            let warning_msg = rows_with_warehouse.map(row =>
                                `Row <span style="color: #ff5858;">${row.idx}</span>: Serial No <span style="color: #ff5858;">${row.custom_serial_noo}</span> already has warehouse <span style="color: #ff5858;">${row.t_warehouse}</span>`
                                ).join('<br>');
                               
 
 
                            let warning_dialog = new frappe.ui.Dialog({
                                title: 'Warning: Existing Warehouse Allocations',
                                fields: [{
                                    fieldname: 'warning_html',
                                    fieldtype: 'HTML',
                                    options: `<div white-space: pre-line;">${warning_msg}</div>`
                                }],
                                primary_action_label: 'Continue Proceed',
                                primary_action() {
                                    updateWarehouses(selected_items, values.target_warehouse);
                                    warning_dialog.hide();
                                    d.hide();
                                },
                                secondary_action_label: 'Skip Allocated Rows',
                                secondary_action() {
                                    let unallocated_rows = selected_items.filter(row => !row.t_warehouse);
                                    updateWarehouses(unallocated_rows, values.target_warehouse);
                                    warning_dialog.hide();
                                    d.hide();
                                }
                            });
 
 
                            warning_dialog.set_secondary_action_label('Skip Allocated Rows');
                            warning_dialog.add_custom_action('Cancel', () => {
                                warning_dialog.hide();
                            }, 'btn-danger');
 
 
                            warning_dialog.show();
                        } else {
                            updateWarehouses(selected_items, values.target_warehouse);
                            d.hide();
                        }
                    }
                });
 
 
                d.show();
            } catch (error) {
                console.error("Error:", error);
                frappe.msgprint("Error processing selected items. Check console for details.");
            }
        }, __('Allocate Locations'));
    }
 });
 
 
 function updateWarehouses(rows, target_warehouse) {
    rows.forEach(row => {
        frappe.model.set_value(row.doctype, row.name, 't_warehouse', target_warehouse);
    });
    cur_frm.refresh();
 }
 
 
 
 
 frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        add_allocate_location_fifo_button(frm);
    }
 });
 
 function add_allocate_location_fifo_button(frm) {
    frm.remove_custom_button("Allocate Location via FIFO");

    frm.add_custom_button(__("Allocate Location via FIFO"), () => {
        const selected_items = frm.doc.items || [];

        if (!selected_items.length) {
            frappe.msgprint(__('No items found in the Stock Entry.'));
            return;
        }

        // Calculate total quantity, ensuring qty is a number
        const total_qty = selected_items.reduce((sum, row) => sum + (row.qty || 0), 0);

        // Group consecutive rows with the same warehouse
        let sequence_groups = [];
        let current_group = {
            warehouse: null,
            start_idx: 0,
            qty: 0
        };

        selected_items.forEach((item, idx) => {
            const warehouse = item.t_warehouse || ''; // Treat null/undefined as empty string
            if (current_group.warehouse !== warehouse) {
                if (current_group.warehouse !== null) {
                    sequence_groups.push({ ...current_group });
                }
                current_group = {
                    warehouse: warehouse,
                    start_idx: idx,
                    qty: item.qty || 0
                };
            } else {
                current_group.qty += item.qty || 0;
            }
        });
        if (current_group.warehouse !== null) {
            sequence_groups.push({ ...current_group });
        }

        // Check if any items have t_warehouse assigned
        const has_warehouse_assignments = sequence_groups.some(group => group.warehouse);

        // Create allocation data
        let allocation_data = [];
        if (!has_warehouse_assignments) {
            // Single row with total quantity if no warehouses assigned
            allocation_data = [{
                id: frappe.utils.get_random(5),
                sequence: '1st',
                quantity: total_qty,
                warehouse: ''
            }];
        } else {
            // Use grouped data if warehouses are assigned
            allocation_data = sequence_groups.map((group, idx) => ({
                id: frappe.utils.get_random(5),
                sequence: `${idx + 1}${getSequenceSuffix(idx + 1)}`,
                quantity: group.qty,
                warehouse: group.warehouse
            }));
        }

        function getSequenceSuffix(num) {
            if (num >= 11 && num <= 13) return 'th';
            switch (num % 10) {
                case 1: return 'st';
                case 2: return 'nd';
                case 3: return 'rd';
                default: return 'th';
            }
        }

        function updateSequences() {
            allocation_data.forEach((row, idx) => {
                const num = idx + 1;
                row.sequence = `${num}${getSequenceSuffix(num)}`;
            });
        }

        const d = new frappe.ui.Dialog({
            title: __('Allocate Location via FIFO'),
            fields: [
                {
                    label: __('Total QTY'),
                    fieldname: 'total_qty',
                    fieldtype: 'Int',
                    read_only: 1,
                    default: total_qty
                },
                {
                    fieldname: 'column',
                    fieldtype: 'Column Break',
                },
                {
                    label: __('Remaining QTY'),
                    fieldname: 'remaining_qty',
                    fieldtype: 'Int',
                    read_only: 1,
                    default: total_qty - allocation_data.reduce((sum, row) => sum + (row.quantity || 0), 0)
                },
                {
                    fieldname: 'section',
                    fieldtype: 'Section Break',
                },
                {
                    fieldname: 'allocation_table',
                    fieldtype: 'Table',
                    label: __('FIFO Allocation'),
                    cannot_add_rows: false,
                    cannot_delete_rows: true,
                    in_place_edit: true,
                    data: allocation_data,
                    get_data: () => allocation_data,
                    fields: [
                        {
                            label: __('Sequence'),
                            fieldname: 'sequence',
                            fieldtype: 'Data',
                            read_only: 1,
                            reqd: 1,
                            in_list_view: 1,
                            columns: 2
                        },
                        {
                            label: __('Quantity'),
                            fieldname: 'quantity',
                            fieldtype: 'Int',
                            reqd: 1,
                            in_list_view: 1,
                            columns: 2,
                            change: function() {
                                const new_total = allocation_data.reduce((sum, row) => sum + (row.quantity || 0), 0);
                                if (new_total > total_qty) {
                                    frappe.msgprint(__('Total allocated quantity ({0}) cannot exceed {1}', [new_total, total_qty]));
                                    this.set_value(0);
                                    d.fields_dict.allocation_table.grid.refresh();
                                }
                                d.set_value('remaining_qty', total_qty - new_total);
                            }
                        },
                        {
                            label: __('Warehouse'),
                            fieldname: 'warehouse',
                            fieldtype: 'Link',
                            options: 'Warehouse',
                            reqd: 1,
                            in_list_view: 1,
                            columns: 4,
                            get_query: () => {
                                return {
                                    filters: [["Warehouse", "custom_type_of_warehouse", "=", "Location"]]
                                };
                            }
                        }
                    ]
                }
            ],
            primary_action_label: __('Proceed'),
            primary_action: (values) => {
                const allocations = values.allocation_table;
                const allocated_total = allocations.reduce((sum, row) => sum + (row.quantity || 0), 0);

                // Filter items up to allocated_total
                let filtered_items = selected_items.filter(row => row.idx >= 1 && row.idx <= allocated_total);
                let rows_with_warehouse = filtered_items.filter(row => row.t_warehouse);

                if (rows_with_warehouse.length) {
                    let warning_msg = rows_with_warehouse.map(row =>
                        `Row <span style="color: #ff5858;">${row.idx}</span>: Serial No <span style="color: #ff5858;">${row.custom_serial_noo}</span> already has warehouse <span style="color: #ff5858;">${row.t_warehouse}</span>`
                    ).join('<br>');

                    let warning_dialog = new frappe.ui.Dialog({
                        title: 'Warning: Existing Warehouse Allocations',
                        fields: [{ fieldname: 'warning_html', fieldtype: 'HTML', options: `<div style="white-space: pre-line;">${warning_msg}</div>` }],
                        primary_action_label: __('Continue & Overwrite'),
                        primary_action: () => {
                            allocateFIFO(filtered_items, allocations, true);
                            warning_dialog.hide();
                            d.hide();
                        },
                        secondary_action_label: __('Skip Already Assigned'),
                        secondary_action: () => {
                            allocateFIFO(filtered_items, allocations, false);
                            warning_dialog.hide();
                            d.hide();
                        }
                    });

                    warning_dialog.add_custom_action('Cancel', () => warning_dialog.hide(), 'btn-danger');
                    warning_dialog.show();
                } else {
                    allocateFIFO(filtered_items, allocations, true);
                    d.hide();
                }
            }
        });

        const grid = d.fields_dict.allocation_table.grid;

        // Add custom buttons
        const buttonContainer = $('<div class="custom-button-container" style="margin-top: 1px; text-align: left;"></div>');
        const removeLastRowBtn = $(`<button class="btn btn-sm btn-default" style="margin-left: 1px;">${__("Remove Last Row")}</button>`);

        removeLastRowBtn.click(function(e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (allocation_data.length > 0) {
                const hasZeroQuantity = allocation_data.some(row => !row.quantity || row.quantity === 0);
                if (hasZeroQuantity) {
                    allocation_data.pop();
                    updateSequences();
                    const new_total = allocation_data.reduce((sum, row) => sum + (row.quantity || 0), 0);
                    d.set_value('remaining_qty', total_qty - new_total);
                    grid.df.data = allocation_data;
                    grid.data = allocation_data;
                    grid.refresh();
                } else {
                    frappe.msgprint(__('The Qty of the last Row should be 0.'));
                }
            } else {
                frappe.msgprint(__('No rows to remove'));
            }
        });

        buttonContainer.append(removeLastRowBtn);
        $(grid.wrapper).after(buttonContainer);

        // Custom delete row handler
        grid.wrapper.on('click', '.grid-remove-rows', function(e) {
            e.preventDefault();
            e.stopImmediatePropagation();

            const selected_rows = grid.get_selected_children();
            if (selected_rows.length) {
                selected_rows.forEach(row => {
                    const index = allocation_data.findIndex(item => item.id === row.id); // Use `id` for consistency
                    if (index > -1) {
                        allocation_data.splice(index, 1);
                    }
                });

                updateSequences();
                const new_total = allocation_data.reduce((sum, row) => sum + (row.quantity || 0), 0);
                d.set_value('remaining_qty', total_qty - new_total);

                grid.df.data = allocation_data;
                grid.data = allocation_data;
                grid.refresh();
                grid.wrapper.find('.grid-row-check').prop('checked', false);
            }
        });

        // Custom add row handler
        grid.add_new_row = function(at, data) {
            const current_total = allocation_data.reduce((sum, row) => sum + (row.quantity || 0), 0);
            const hasZeroQuantity = allocation_data.some(row => !row.quantity || row.quantity === 0);

            if (hasZeroQuantity) {
                frappe.msgprint(__('Cannot add more rows: Please fill in quantity for existing rows'));
                return;
            }

            if (current_total >= total_qty) {
                frappe.msgprint(__('Cannot add more rows: Total quantity reached'));
                return;
            }

            const new_sequence = allocation_data.length + 1;
            const new_row = {
                id: frappe.utils.get_random(5),
                sequence: `${new_sequence}${getSequenceSuffix(new_sequence)}`,
                quantity: 0,
                warehouse: ''
            };

            if (typeof at === "number") {
                allocation_data.splice(at, 0, new_row);
            } else {
                allocation_data.push(new_row);
            }

            updateSequences();
            grid.df.data = allocation_data;
            grid.data = allocation_data;
            grid.refresh();

            return new_row;
        };

        d.show();
    }, __('Allocate Locations'));
}

function allocateFIFO(selected_items, allocations, overwrite_existing) {
    let row_idx = 0;

    allocations.forEach(alloc => {
        let remaining_alloc_qty = alloc.quantity;

        while (remaining_alloc_qty > 0 && row_idx < selected_items.length) {
            const item_row = selected_items[row_idx];

            if (!item_row.t_warehouse || overwrite_existing) {
                const qty_to_assign = Math.min(item_row.qty, remaining_alloc_qty);

                frappe.model.set_value(item_row.doctype, item_row.name, {
                    t_warehouse: alloc.warehouse,
                    allocated_qty: qty_to_assign
                });

                remaining_alloc_qty -= qty_to_assign;
            }

            row_idx++;
        }
    });

    cur_frm.refresh();
}


 
 