# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, date_diff


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "school",
            "label": _("School"),
            "fieldtype": "Link",
            "options": "School",
            "width": 200
        },
        {
            "fieldname": "distribution",
            "label": _("Distribution"),
            "fieldtype": "Link",
            "options": "Book Sample Distribution",
            "width": 120
        },
        {
            "fieldname": "distribution_date",
            "label": _("Distribution Date"),
            "fieldtype": "Date",
            "width": 110
        },
        {
            "fieldname": "item_code",
            "label": _("Book"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },
        {
            "fieldname": "item_name",
            "label": _("Book Name"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "class_grade",
            "label": _("Class"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "qty_distributed",
            "label": _("Distributed"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "qty_collected",
            "label": _("Collected"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "qty_pending",
            "label": _("Pending"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "expected_return_date",
            "label": _("Expected Return"),
            "fieldtype": "Date",
            "width": 110
        },
        {
            "fieldname": "days_overdue",
            "label": _("Days Overdue"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "distributor_name",
            "label": _("Distributor"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "area_zone",
            "label": _("Area/Zone"),
            "fieldtype": "Data",
            "width": 120
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            bsd.school,
            bsd.name as distribution,
            bsd.distribution_date,
            bsdi.item_code,
            bsdi.item_name,
            bsdi.class_grade,
            bsdi.qty as qty_distributed,
            COALESCE(bsdi.qty_collected, 0) as qty_collected,
            (bsdi.qty - COALESCE(bsdi.qty_collected, 0)) as qty_pending,
            bsdi.expected_return_date,
            bsd.distributor_name,
            s.area_zone
        FROM `tabBook Sample Distribution` bsd
        INNER JOIN `tabBook Sample Distribution Item` bsdi ON bsdi.parent = bsd.name
        INNER JOIN `tabSchool` s ON s.name = bsd.school
        WHERE bsd.docstatus = 1
        AND bsd.status IN ('Distributed', 'Partially Collected')
        AND (bsdi.qty - COALESCE(bsdi.qty_collected, 0)) > 0
        {conditions}
        ORDER BY bsdi.expected_return_date, bsd.distribution_date
    """.format(conditions=conditions), filters, as_dict=True)

    # Calculate days overdue
    today = getdate()
    for row in data:
        if row.expected_return_date:
            days = date_diff(today, row.expected_return_date)
            row["days_overdue"] = days if days > 0 else 0
        else:
            row["days_overdue"] = 0

    return data


def get_conditions(filters):
    conditions = []

    if filters.get("school"):
        conditions.append("AND bsd.school = %(school)s")

    if filters.get("from_date"):
        conditions.append("AND bsd.distribution_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("AND bsd.distribution_date <= %(to_date)s")

    if filters.get("item_code"):
        conditions.append("AND bsdi.item_code = %(item_code)s")

    if filters.get("class_grade"):
        conditions.append("AND bsdi.class_grade = %(class_grade)s")

    if filters.get("area_zone"):
        conditions.append("AND s.area_zone = %(area_zone)s")

    if filters.get("overdue_only"):
        conditions.append("AND bsdi.expected_return_date < CURDATE()")

    return " ".join(conditions)
