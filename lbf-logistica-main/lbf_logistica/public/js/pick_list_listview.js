frappe.listview_settings['Pick List'] = {
    onload: function (listview) {
        // Add 'Mark As Complete' action item
        listview.page.add_action_item(__('Mark As Complete'), function () {
            const selected_docs = listview.get_checked_items();
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select at least one Pick List.'));
                return;
            }
            open_stock_transfer_dialog(selected_docs);
        });
 
        // Hide default status field
        listview.page.fields_dict.status.$wrapper.hide();
    },
 
    // Custom formatters for fields
    formatters: {
        custom_pl_status: (value) => {
            const status_colors = {
                "Open": "orange",
                "In Progress": "blue",
                "Completed": "green",
                "Cancelled": "red"
            };
            const color = status_colors[value] || "gray"; // Default to gray if status not found
            return `<span class="indicator-pill ${color}">${value}</span>`;
        }
    }
 };
 
 function open_stock_transfer_dialog(selected_docs) {
    let items = [];
 
    // Fetch data for all selected Pick Lists
    let promises = selected_docs.map(doc => {
        return frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Pick List",
                name: doc.name
            }
        }).then(response => {
            const pick_list = response.message;
            const default_loading_warehouse = pick_list.custom_loading_zone || '';  // Get from custom_loading_zone in Pick List
            pick_list.custom_item_locations.forEach(item => {
                items.push({
                    pick_list_id: pick_list.name,
                    item_code: item.item_code,
                    target_warehouse: item.target_warehouse || default_loading_warehouse,
                    source_warehouse: item.location || '',
                    uom: item.stock_uom,
                    qty: item.qty,
                    batch_no: item.batch_no || '',
                    serial_no: item.serial_no || '',
                    description: item.description || ''
                });
            });
        });
    });
 
    Promise.all(promises).then(() => {
        let d = new frappe.ui.Dialog({
            title: 'Stock Transfer',
            size: 'large',
            fields: [
                {
                    fieldname: 'items',
                    fieldtype: 'Table',
                    label: 'Pick List Items',
                    cannot_add_rows: true,
                    in_place_edit: false,
                    fields: [
                        { fieldtype: 'Data', fieldname: 'pick_list_id', label: 'Pick List ID', in_list_view: 1, read_only: 1 },
                        { fieldtype: 'Data', fieldname: 'item_code', label: 'Item Code', in_list_view: 1, read_only: 1 },
                        { fieldtype: 'Link', fieldname: 'source_warehouse', label: 'Source Warehouse', options: 'Warehouse', in_list_view: 1 },
                        { fieldtype: 'Link', fieldname: 'target_warehouse', label: 'Target Warehouse', options: 'Warehouse', in_list_view: 1,
                            get_query: () => {
                                return {
                                    filters: [
                                        ["Warehouse", "custom_type_of_warehouse", "in", ["Loading Zone", "Both Loading and Un-Loading Zone"]]
                                    ]
                                };
                            }
                        
                         },
                        { fieldtype: 'Data', fieldname: 'uom', label: 'UOM', in_list_view: 1, read_only: 1 },
                        { fieldtype: 'Float', fieldname: 'qty', label: 'Qty', in_list_view: 1 },
                        { fieldtype: 'Link', fieldname: 'batch_no', label: 'Batch No', options: 'Batch', in_list_view: 1, read_only: 1 },
                        { fieldtype: 'Link', fieldname: 'serial_no', label: 'Serial No', options: 'Serial No', in_list_view: 1, read_only: 1 }
                    ]
                }
            ],
            primary_action_label: 'Proceed',
            primary_action(values) {
                frappe.confirm(
                    __('Are you sure you want to create Stock Entries for the selected items?'),
                    function () {
                        create_combined_stock_entries(values.items);
                    }
                );
                d.hide();
            }
        });
 
        d.fields_dict.items.df.data = items;
        d.fields_dict.items.grid.refresh();
        d.show();
    });
 }
 
 function create_combined_stock_entries(items) {
    let grouped_items = {};
 
    // Group items by Pick List ID
    items.forEach(item => {
        if (!grouped_items[item.pick_list_id]) {
            grouped_items[item.pick_list_id] = [];
        }
        grouped_items[item.pick_list_id].push(item);
    });
 
    // Create stock entry for each Pick List
    Object.keys(grouped_items).forEach(pick_list_id => {
        frappe.call({
            method: 'lbf_logistica.overrides.pick_list.create_stock_entries',
            args: {
                pick_list_id: pick_list_id,
                items: grouped_items[pick_list_id]
            },
            callback: function (response) {
                if (response.message) {
                    frappe.msgprint(__('Stock Entry created successfully: {0}', [response.message]));
                }
            }
        });
    });
 }
 
 
 

