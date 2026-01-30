# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "voucher_type",
            "label": _("Type"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "voucher_no",
            "label": _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 150
        },
        {
            "fieldname": "item_code",
            "label": _("Book"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 180
        },
        {
            "fieldname": "item_name",
            "label": _("Book Name"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "class_grade",
            "label": _("Class"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "school",
            "label": _("School"),
            "fieldtype": "Link",
            "options": "School",
            "width": 150
        },
        {
            "fieldname": "vehicle",
            "label": _("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 120
        },
        {
            "fieldname": "qty_in",
            "label": _("Qty In"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "qty_out",
            "label": _("Qty Out"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "balance",
            "label": _("Balance"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "warehouse",
            "label": _("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = []

    # Get Loading entries (books loaded to van - OUT from source, IN to van)
    loading_data = frappe.db.sql("""
        SELECT
            bsl.loading_date as date,
            'Book Sample Loading' as voucher_type,
            bsl.name as voucher_no,
            bsli.item_code,
            bsli.item_name,
            bsli.class_grade,
            NULL as school,
            bsl.vehicle,
            bsli.qty as qty_out,
            0 as qty_in,
            bsl.source_warehouse as warehouse,
            'Loading to Van' as remarks
        FROM `tabBook Sample Loading` bsl
        INNER JOIN `tabBook Sample Loading Item` bsli ON bsli.parent = bsl.name
        WHERE bsl.docstatus = 1
        {conditions}
        ORDER BY bsl.loading_date, bsl.creation
    """.format(conditions=conditions.get("loading", "")), filters, as_dict=True)

    # Get Distribution entries (books distributed to school - OUT from van)
    distribution_data = frappe.db.sql("""
        SELECT
            bsd.distribution_date as date,
            'Book Sample Distribution' as voucher_type,
            bsd.name as voucher_no,
            bsdi.item_code,
            bsdi.item_name,
            bsdi.class_grade,
            bsd.school,
            bsd.vehicle,
            0 as qty_in,
            bsdi.qty as qty_out,
            bsd.source_warehouse as warehouse,
            'Distributed to School' as remarks
        FROM `tabBook Sample Distribution` bsd
        INNER JOIN `tabBook Sample Distribution Item` bsdi ON bsdi.parent = bsd.name
        WHERE bsd.docstatus = 1
        {conditions}
        ORDER BY bsd.distribution_date, bsd.creation
    """.format(conditions=conditions.get("distribution", "")), filters, as_dict=True)

    # Get Collection entries (books collected from school - IN to van/warehouse)
    collection_data = frappe.db.sql("""
        SELECT
            bsc.collection_date as date,
            'Book Sample Collection' as voucher_type,
            bsc.name as voucher_no,
            bsci.item_code,
            bsci.item_name,
            bsci.class_grade,
            bsc.school,
            bsc.vehicle,
            bsci.qty_collected as qty_in,
            0 as qty_out,
            bsc.target_warehouse as warehouse,
            'Collected from School' as remarks
        FROM `tabBook Sample Collection` bsc
        INNER JOIN `tabBook Sample Collection Item` bsci ON bsci.parent = bsc.name
        WHERE bsc.docstatus = 1
        AND bsci.qty_collected > 0
        {conditions}
        ORDER BY bsc.collection_date, bsc.creation
    """.format(conditions=conditions.get("collection", "")), filters, as_dict=True)

    # Combine all data
    all_data = loading_data + distribution_data + collection_data

    # Sort by date
    all_data.sort(key=lambda x: (x.get("date") or "", x.get("voucher_no") or ""))

    # Calculate running balance per item
    item_balances = {}
    for row in all_data:
        item = row.get("item_code")
        if item not in item_balances:
            item_balances[item] = 0

        qty_in = flt(row.get("qty_in", 0))
        qty_out = flt(row.get("qty_out", 0))
        item_balances[item] += qty_in - qty_out
        row["balance"] = item_balances[item]
        data.append(row)

    return data


def get_conditions(filters):
    conditions = {
        "loading": [],
        "distribution": [],
        "collection": []
    }

    if filters.get("from_date"):
        conditions["loading"].append("AND bsl.loading_date >= %(from_date)s")
        conditions["distribution"].append("AND bsd.distribution_date >= %(from_date)s")
        conditions["collection"].append("AND bsc.collection_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions["loading"].append("AND bsl.loading_date <= %(to_date)s")
        conditions["distribution"].append("AND bsd.distribution_date <= %(to_date)s")
        conditions["collection"].append("AND bsc.collection_date <= %(to_date)s")

    if filters.get("item_code"):
        conditions["loading"].append("AND bsli.item_code = %(item_code)s")
        conditions["distribution"].append("AND bsdi.item_code = %(item_code)s")
        conditions["collection"].append("AND bsci.item_code = %(item_code)s")

    if filters.get("vehicle"):
        conditions["loading"].append("AND bsl.vehicle = %(vehicle)s")
        conditions["distribution"].append("AND bsd.vehicle = %(vehicle)s")
        conditions["collection"].append("AND bsc.vehicle = %(vehicle)s")

    if filters.get("school"):
        conditions["distribution"].append("AND bsd.school = %(school)s")
        conditions["collection"].append("AND bsc.school = %(school)s")

    return {
        "loading": " ".join(conditions["loading"]),
        "distribution": " ".join(conditions["distribution"]),
        "collection": " ".join(conditions["collection"])
    }
