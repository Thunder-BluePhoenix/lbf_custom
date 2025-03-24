frappe.ui.form.on('Driver', {
    custom_first_name: function(frm) {
        set_full_name(frm);
    },
    custom_last_name: function(frm) {
        set_full_name(frm);
    }
});

function set_full_name(frm) {
    if (frm.doc.custom_first_name || frm.doc.custom_last_name) {
        frm.set_value('full_name', (frm.doc.custom_first_name|| '') + ' ' + (frm.doc.custom_last_name || ''));
    }
}
