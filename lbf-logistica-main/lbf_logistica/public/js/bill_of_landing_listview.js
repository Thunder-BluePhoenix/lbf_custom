frappe.listview_settings['Bill Of Landing'] = {
    refersh: function(listview) {
        

        const printButton = listview.page.add_action_item(__('Print Labels'), function() {
            
            const selected_docs = listview.get_checked_items();
          
            
            if (selected_docs.length === 1) {
                frappe.model.with_doctype('Bill Of Landing', function() {
                    var w = window.open(
                        frappe.urllib.get_full_url(
                            '/printview?doctype=' + 
                            encodeURIComponent('Bill Of Landing') +
                            '&name=' + 
                            encodeURIComponent(selected_docs[0].name) +
                            '&trigger_print=1' +
                            '&format=' + 
                            encodeURIComponent('BOL Stickers') +
                            '&no_letterhead=0'
                        )
                    );
                    if (!w) {
                        frappe.msgprint(__("Please enable pop-ups"));
                    }
                });
            }
        });
        
       
        $(printButton).hide();
        

        // Use the onselect event to listen for selection changes
        listview.onselect = function() {
            const selected_docs = listview.get_checked_items();
            if (selected_docs.length === 1) {
                $(printButton).show();
            } else {
                $(printButton).hide();
            }
        
        };
    }
};