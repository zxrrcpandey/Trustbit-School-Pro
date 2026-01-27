// Trustbit School Pro - Custom JavaScript

frappe.provide("trustbit_school_pro");

// Utility functions for the app
trustbit_school_pro.utils = {
    // Format quantity with color based on pending status
    format_qty_status: function(qty_pending, qty_total) {
        if (qty_pending <= 0) {
            return `<span class="text-success">${qty_pending}</span>`;
        } else if (qty_pending < qty_total) {
            return `<span class="text-warning">${qty_pending}</span>`;
        } else {
            return `<span class="text-danger">${qty_pending}</span>`;
        }
    },

    // Check if date is overdue
    is_overdue: function(date) {
        if (!date) return false;
        return frappe.datetime.get_diff(date, frappe.datetime.get_today()) < 0;
    },

    // Get status color
    get_status_color: function(status) {
        const colors = {
            'Draft': 'orange',
            'Loaded': 'blue',
            'In Transit': 'purple',
            'Returned': 'green',
            'Distributed': 'blue',
            'Partially Collected': 'yellow',
            'Fully Collected': 'green',
            'Collected': 'green',
            'Pending': 'orange',
            'Partial': 'yellow',
            'Cancelled': 'red'
        };
        return colors[status] || 'gray';
    }
};

// Custom button for quick collection from distribution
$(document).on('app_ready', function() {
    // Add custom action to Book Sample Distribution list
    if (frappe.listview_settings['Book Sample Distribution']) {
        frappe.listview_settings['Book Sample Distribution'].onload = function(listview) {
            listview.page.add_action_item(__('Create Collection'), function() {
                const selected = listview.get_checked_items();
                if (selected.length !== 1) {
                    frappe.msgprint(__('Please select exactly one distribution'));
                    return;
                }
                frappe.call({
                    method: 'trustbit_school_pro.trustbit_school_pro.doctype.book_sample_collection.book_sample_collection.make_collection_from_distribution',
                    args: { distribution: selected[0].name },
                    callback: function(r) {
                        if (r.message) {
                            frappe.model.sync(r.message);
                            frappe.set_route('Form', 'Book Sample Collection', r.message.name);
                        }
                    }
                });
            });
        };
    }
});
