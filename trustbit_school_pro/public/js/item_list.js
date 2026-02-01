// Item List - Add Barcode Filter
// Trustbit School Pro

frappe.listview_settings['Item'] = frappe.listview_settings['Item'] || {};

// Store original onload if exists
const original_onload = frappe.listview_settings['Item'].onload;

frappe.listview_settings['Item'].onload = function(listview) {
    // Call original onload if exists
    if (original_onload) {
        original_onload(listview);
    }

    // Add Barcode filter
    listview.page.add_field({
        fieldname: 'barcode',
        label: __('Barcode'),
        fieldtype: 'Data',
        onchange: function() {
            let barcode = this.get_value();
            if (barcode) {
                // Search for item by barcode
                frappe.call({
                    method: 'trustbit_school_pro.api.get_item_by_barcode',
                    args: { barcode: barcode },
                    callback: function(r) {
                        if (r.message) {
                            // Filter by the found item
                            listview.filter_area.add([[listview.doctype, 'name', '=', r.message]]);
                        } else {
                            frappe.show_alert({
                                message: __('No item found with barcode: {0}', [barcode]),
                                indicator: 'orange'
                            }, 3);
                        }
                    }
                });
            } else {
                // Clear the name filter if barcode is empty
                listview.filter_area.remove('name');
            }
        }
    });
};
