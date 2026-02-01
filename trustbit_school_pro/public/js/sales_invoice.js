// Sales Invoice Customizations
// Trustbit School Pro

frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        // Auto-check "Update Stock" for new Sales Invoices
        if (frm.is_new()) {
            frm.set_value('update_stock', 1);
        }
    },

    refresh: function(frm) {
        // Also ensure it's checked on refresh for new documents
        if (frm.is_new() && !frm.doc.update_stock) {
            frm.set_value('update_stock', 1);
        }
    }
});
