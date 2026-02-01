// Item List - Add Barcode Search
// Trustbit School Pro

frappe.listview_settings['Item'] = frappe.listview_settings['Item'] || {};

// Store original onload if exists
const original_onload = frappe.listview_settings['Item'].onload;

frappe.listview_settings['Item'].onload = function(listview) {
    // Call original onload if exists
    if (original_onload) {
        original_onload(listview);
    }

    // Add Barcode search button
    listview.page.add_inner_button(__('Search by Barcode'), function() {
        frappe.prompt([
            {
                label: __('Barcode'),
                fieldname: 'barcode',
                fieldtype: 'Data',
                reqd: 1,
                description: __('Enter or scan barcode')
            }
        ], function(values) {
            if (values.barcode) {
                frappe.call({
                    method: 'trustbit_school_pro.api.get_item_by_barcode',
                    args: { barcode: values.barcode },
                    callback: function(r) {
                        if (r.message) {
                            // Open the item directly
                            frappe.set_route('Form', 'Item', r.message);
                        } else {
                            frappe.msgprint({
                                title: __('Not Found'),
                                message: __('No item found with barcode: {0}', [values.barcode]),
                                indicator: 'orange'
                            });
                        }
                    }
                });
            }
        }, __('Search Item by Barcode'), __('Search'));
    });
};
