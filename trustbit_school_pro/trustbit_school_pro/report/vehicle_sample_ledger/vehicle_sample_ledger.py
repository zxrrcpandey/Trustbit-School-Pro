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
            "width": 130
        },
        {
            "fieldname": "voucher_no",
            "label": _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
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
            "fieldname": "driver_name",
            "label": _("Driver"),
            "fieldtype": "Data",
            "width": 120
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
            "width": 150
        },
        {
            "fieldname": "item_name",
            "label": _("Book Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "qty_loaded",
            "label": _("Loaded"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "qty_distributed",
            "label": _("Dist"),
            "fieldtype": "Float",
            "width": 70
        },
        {
            "fieldname": "qty_collected",
            "label": _("Coll"),
            "fieldtype": "Float",
            "width": 70
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
            "width": 130
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)
    data = []

    # Get Loading entries (books loaded to van)
    loading_data = frappe.db.sql("""
        SELECT
            bsl.loading_date as date,
            'Book Sample Loading' as voucher_type,
            bsl.name as voucher_no,
            bsl.vehicle,
            bsl.driver_name,
            NULL as school,
            bsli.item_code,
            bsli.item_name,
            bsli.qty as qty_loaded,
            0 as qty_distributed,
            0 as qty_collected,
            bsl.source_warehouse as warehouse
        FROM `tabBook Sample Loading` bsl
        INNER JOIN `tabBook Sample Loading Item` bsli ON bsli.parent = bsl.name
        WHERE bsl.docstatus = 1
        {conditions}
        ORDER BY bsl.loading_date, bsl.creation
    """.format(conditions=conditions.get("loading", "")), filters, as_dict=True)

    # Get Distribution entries (books distributed to school)
    distribution_data = frappe.db.sql("""
        SELECT
            bsd.distribution_date as date,
            'Book Sample Distribution' as voucher_type,
            bsd.name as voucher_no,
            bsd.vehicle,
            bsd.distributor_name as driver_name,
            bsd.school,
            bsdi.item_code,
            bsdi.item_name,
            0 as qty_loaded,
            bsdi.qty as qty_distributed,
            0 as qty_collected,
            bsd.source_warehouse as warehouse
        FROM `tabBook Sample Distribution` bsd
        INNER JOIN `tabBook Sample Distribution Item` bsdi ON bsdi.parent = bsd.name
        WHERE bsd.docstatus = 1
        {conditions}
        ORDER BY bsd.distribution_date, bsd.creation
    """.format(conditions=conditions.get("distribution", "")), filters, as_dict=True)

    # Get Collection entries (books collected from school)
    # Note: Book Sample Collection doesn't have vehicle field
    collection_data = frappe.db.sql("""
        SELECT
            bsc.collection_date as date,
            'Book Sample Collection' as voucher_type,
            bsc.name as voucher_no,
            NULL as vehicle,
            bsc.collector_name as driver_name,
            bsc.school,
            bsci.item_code,
            bsci.item_name,
            0 as qty_loaded,
            0 as qty_distributed,
            bsci.qty_collected as qty_collected,
            bsc.target_warehouse as warehouse
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

    # Calculate running balance per vehicle
    # Balance = Loaded - Distributed + Collected (books currently in vehicle)
    vehicle_balances = {}
    for row in all_data:
        vehicle = row.get("vehicle")
        if vehicle not in vehicle_balances:
            vehicle_balances[vehicle] = 0

        qty_loaded = flt(row.get("qty_loaded", 0))
        qty_distributed = flt(row.get("qty_distributed", 0))
        qty_collected = flt(row.get("qty_collected", 0))

        # Loaded adds to vehicle, distributed removes, collected adds back
        vehicle_balances[vehicle] += qty_loaded - qty_distributed + qty_collected
        row["balance"] = vehicle_balances[vehicle]
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

    if filters.get("vehicle"):
        conditions["loading"].append("AND bsl.vehicle = %(vehicle)s")
        conditions["distribution"].append("AND bsd.vehicle = %(vehicle)s")
        # Note: Book Sample Collection doesn't have vehicle field

    if filters.get("item_code"):
        conditions["loading"].append("AND bsli.item_code = %(item_code)s")
        conditions["distribution"].append("AND bsdi.item_code = %(item_code)s")
        conditions["collection"].append("AND bsci.item_code = %(item_code)s")

    if filters.get("school"):
        conditions["distribution"].append("AND bsd.school = %(school)s")
        conditions["collection"].append("AND bsc.school = %(school)s")

    return {
        "loading": " ".join(conditions["loading"]),
        "distribution": " ".join(conditions["distribution"]),
        "collection": " ".join(conditions["collection"])
    }
