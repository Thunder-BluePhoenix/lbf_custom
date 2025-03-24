frappe.ui.form.on('Pricing Rule', {
    onload: function(frm) {
        // Restrict options for 'apply_on' field to 'Item Code', 'Item Group', and 'Brand'
        frm.set_df_property('apply_on', 'options', [
            '',
            'Item Code',
            'Item Group',
            'Brand'
        ]);
    }
});
