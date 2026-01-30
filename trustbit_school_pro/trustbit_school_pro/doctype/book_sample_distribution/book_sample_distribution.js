// Copyright (c) 2024, Trustbit Software and contributors
// For license information, please see license.txt

frappe.ui.form.on('Book Sample Distribution', {
    refresh: function(frm) {
        // Add button to create collection
        if (frm.doc.docstatus === 1 && frm.doc.status !== 'Fully Collected') {
            frm.add_custom_button(__('Create Collection'), function() {
                frappe.model.open_mapped_doc({
                    method: 'trustbit_school_pro.trustbit_school_pro.doctype.book_sample_collection.book_sample_collection.make_collection_from_distribution',
                    frm: frm
                });
            }, __('Actions'));
        }
    }
});

frappe.ui.form.on('Book Sample Distribution Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code) {
            // Fetch class grades for the item
            frappe.call({
                method: 'trustbit_school_pro.trustbit_school_pro.doctype.book_sample_loading.book_sample_loading.get_item_class_grades',
                args: { item_code: row.item_code },
                callback: function(r) {
                    if (r.message !== undefined) {
                        frappe.model.set_value(cdt, cdn, 'class_grade', r.message);
                    }
                }
            });
        }
    },

    items_add: function(frm, cdt, cdn) {
        // Set default qty
        frappe.model.set_value(cdt, cdn, 'qty', 1);
    }
});
