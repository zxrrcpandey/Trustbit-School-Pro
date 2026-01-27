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
        if (row.item_code && frm.doc.source_warehouse) {
            update_available_qty_row(frm, row, cdt, cdn);
        }
    },

    items_add: function(frm, cdt, cdn) {
        // Set default qty
        frappe.model.set_value(cdt, cdn, 'qty', 1);
    }
});

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
