// Copyright (c) 2024, Trustbit Software and contributors
// For license information, please see license.txt

frappe.ui.form.on('Book Sample Loading', {
    refresh: function(frm) {
        // Update available qty for all items when form is refreshed
        if (frm.doc.source_warehouse) {
            frm.doc.items.forEach(function(item, idx) {
                if (item.item_code) {
                    update_available_qty(frm, item.item_code, idx);
                }
            });
        }
    },

    source_warehouse: function(frm) {
        // Update available qty for all items when source warehouse changes
        frm.doc.items.forEach(function(item, idx) {
            if (item.item_code) {
                update_available_qty(frm, item.item_code, idx);
            }
        });
    }
});

frappe.ui.form.on('Book Sample Loading Item', {
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

            // Fetch available qty
            if (frm.doc.source_warehouse) {
                update_available_qty_row(frm, row, cdt, cdn);
            }
        }
    },

    class_grade: function(frm, cdt, cdn) {
        // Open multiselect dialog when class_grade field is clicked/edited
        show_class_grade_dialog(frm, cdt, cdn);
    },

    items_add: function(frm, cdt, cdn) {
        // Set default qty
        frappe.model.set_value(cdt, cdn, 'qty', 1);
    }
});

function show_class_grade_dialog(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let current_values = row.class_grade ? row.class_grade.split(', ').map(v => v.trim()) : [];

    // Fetch all class grades
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Class Grade',
            filters: { is_active: 1 },
            fields: ['name', 'class_order'],
            limit_page_length: 0
        },
        callback: function(r) {
            if (r.message) {
                // Sort by class_order
                let sorted = r.message.sort((a, b) => (a.class_order || 0) - (b.class_order || 0));
                let options = sorted.map(cg => ({
                    label: cg.name,
                    value: cg.name,
                    checked: current_values.includes(cg.name)
                }));

                let d = new frappe.ui.Dialog({
                    title: __('Select Class/Grade'),
                    fields: [
                        {
                            fieldname: 'class_grades',
                            fieldtype: 'MultiCheck',
                            label: __('Class/Grades'),
                            options: options,
                            columns: 3
                        }
                    ],
                    primary_action_label: __('Select'),
                    primary_action: function(values) {
                        let selected = values.class_grades || [];
                        frappe.model.set_value(cdt, cdn, 'class_grade', selected.join(', '));
                        d.hide();
                    }
                });
                d.show();
            }
        }
    });
}

function update_available_qty(frm, item_code, idx) {
    frappe.call({
        method: 'trustbit_school_pro.trustbit_school_pro.doctype.book_sample_loading.book_sample_loading.get_stock_balance_api',
        args: {
            item_code: item_code,
            warehouse: frm.doc.source_warehouse
        },
        callback: function(r) {
            if (r.message !== undefined) {
                frm.doc.items[idx].available_qty = r.message;
                frm.refresh_field('items');
            }
        }
    });
}

function update_available_qty_row(frm, row, cdt, cdn) {
    frappe.call({
        method: 'trustbit_school_pro.trustbit_school_pro.doctype.book_sample_loading.book_sample_loading.get_stock_balance_api',
        args: {
            item_code: row.item_code,
            warehouse: frm.doc.source_warehouse
        },
        callback: function(r) {
            if (r.message !== undefined) {
                frappe.model.set_value(cdt, cdn, 'available_qty', r.message);
            }
        }
    });
}
