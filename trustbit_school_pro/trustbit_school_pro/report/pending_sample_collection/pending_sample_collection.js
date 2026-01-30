// Copyright (c) 2024, Trustbit Software and contributors
// For license information, please see license.txt

frappe.query_reports["Pending Sample Collection"] = {
    "filters": [
        {
            "fieldname": "school",
            "label": __("School"),
            "fieldtype": "Link",
            "options": "School"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "item_code",
            "label": __("Book"),
            "fieldtype": "Link",
            "options": "Item",
            "get_query": function() {
                return {
                    filters: {
                        "custom_is_sample_book": 1
                    }
                };
            }
        },
        {
            "fieldname": "class_grade",
            "label": __("Class/Grade"),
            "fieldtype": "Link",
            "options": "Class Grade"
        },
        {
            "fieldname": "area_zone",
            "label": __("Area/Zone"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "overdue_only",
            "label": __("Overdue Only"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname == "qty_pending" && data.qty_pending > 0) {
            value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
        }

        if (column.fieldname == "days_overdue" && data.days_overdue > 0) {
            value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
        }

        return value;
    }
};
