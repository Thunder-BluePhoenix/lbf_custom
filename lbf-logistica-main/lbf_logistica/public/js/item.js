frappe.ui.form.on('Item', {
    item_code: function (frm) {
        if (frm.doc.item_code) {
            // Automatically populate fields when Item Code is entered
            frm.set_value('has_batch_no', 1);
            frm.set_value('has_serial_no', 1);
            frm.set_value('create_new_batch', 1);
            frm.set_value('batch_number_series', frm.doc.batch_number_series || 'BN.########');
            frm.set_value('serial_no_series', frm.doc.serial_no_series || 'SN.########');
        }
    },
});
