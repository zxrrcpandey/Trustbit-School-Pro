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
            "width": 150
        },
        {
            "fieldname": "voucher_no",
            "label": _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 150
        },
        {
            "fieldname": "school",
            "label": _("School"),
            "fieldtype": "Link",
            "options": "School",
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
            "width": 150
        },
        {
            "fieldname": "class_grade",
            "label": _("Class"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "qty_given",
            "label": _("Given"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "qty_returned",
            "label": _("Returned"),
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
            "fieldname": "distributor",
            "label": _("Distributor"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "area_zone",
            "label": _("Area/Zone"),
            "fieldtype": "Data",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = []

    # Get Distribution entries (books given to school)
    distribution_data = frappe.db.sql("""
        SELECT
            bsd.distribution_date as date,
            'Book Sample Distribution' as voucher_type,
            bsd.name as voucher_no,
            bsd.school,
            bsdi.item_code,
            bsdi.item_name,
            bsdi.class_grade,
            bsdi.qty as qty_given,
            0 as qty_returned,
            bsd.distributor_name as distributor,
            s.area_zone
        FROM `tabBook Sample Distribution` bsd
        INNER JOIN `tabBook Sample Distribution Item` bsdi ON bsdi.parent = bsd.name
        INNER JOIN `tabSchool` s ON s.name = bsd.school
        WHERE bsd.docstatus = 1
        {conditions}
        ORDER BY bsd.distribution_date, bsd.creation
    """.format(conditions=conditions.get("distribution", "")), filters, as_dict=True)

    # Get Collection entries (books returned from school)
    collection_data = frappe.db.sql("""
        SELECT
            bsc.collection_date as date,
            'Book Sample Collection' as voucher_type,
            bsc.name as voucher_no,
            bsc.school,
            bsci.item_code,
            bsci.item_name,
            bsci.class_grade,
            0 as qty_given,
            bsci.qty_collected as qty_returned,
            bsc.collector_name as distributor,
            s.area_zone
        FROM `tabBook Sample Collection` bsc
        INNER JOIN `tabBook Sample Collection Item` bsci ON bsci.parent = bsc.name
        INNER JOIN `tabSchool` s ON s.name = bsc.school
        WHERE bsc.docstatus = 1
        AND bsci.qty_collected > 0
        {conditions}
        ORDER BY bsc.collection_date, bsc.creation
    """.format(conditions=conditions.get("collection", "")), filters, as_dict=True)

    # Combine all data
    all_data = distribution_data + collection_data

    # Sort by school and date
    all_data.sort(key=lambda x: (x.get("school") or "", x.get("date") or "", x.get("voucher_no") or ""))

    # Calculate running balance per school+item
    school_item_balances = {}
    for row in all_data:
        key = (row.get("school"), row.get("item_code"))
        if key not in school_item_balances:
            school_item_balances[key] = 0

        qty_given = flt(row.get("qty_given", 0))
        qty_returned = flt(row.get("qty_returned", 0))
        school_item_balances[key] += qty_given - qty_returned
        row["balance"] = school_item_balances[key]
        data.append(row)

    return data


def get_conditions(filters):
    conditions = {
        "distribution": [],
        "collection": []
    }

    if filters.get("from_date"):
        conditions["distribution"].append("AND bsd.distribution_date >= %(from_date)s")
        conditions["collection"].append("AND bsc.collection_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions["distribution"].append("AND bsd.distribution_date <= %(to_date)s")
        conditions["collection"].append("AND bsc.collection_date <= %(to_date)s")

    if filters.get("school"):
        conditions["distribution"].append("AND bsd.school = %(school)s")
        conditions["collection"].append("AND bsc.school = %(school)s")

    if filters.get("item_code"):
        conditions["distribution"].append("AND bsdi.item_code = %(item_code)s")
        conditions["collection"].append("AND bsci.item_code = %(item_code)s")

    if filters.get("area_zone"):
        conditions["distribution"].append("AND s.area_zone = %(area_zone)s")
        conditions["collection"].append("AND s.area_zone = %(area_zone)s")

    return {
        "distribution": " ".join(conditions["distribution"]),
        "collection": " ".join(conditions["collection"])
    }
