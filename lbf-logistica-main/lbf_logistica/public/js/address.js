frappe.ui.form.on('Address', {
    onload: function(frm) {
        frm.set_query('custom_warehouse', function () {
            return {
                filters: {
                    custom_type_of_warehouse: ['in', ['Loading Zone', 'Both Loading and Un-Loading Zone']]
                }
            };
        });

    }
});