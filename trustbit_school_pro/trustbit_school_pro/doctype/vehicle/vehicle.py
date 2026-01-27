# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Vehicle(Document):
    def after_insert(self):
        """Create warehouse for this vehicle"""
        if not self.warehouse:
            create_vehicle_warehouse(self, None)


def create_vehicle_warehouse(doc, method):
    """Create a warehouse for the vehicle"""
    if doc.warehouse:
        return

    # Get default company
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        company = frappe.db.get_value("Company", {}, "name")

    if not company:
        frappe.throw("Please set up a company first")

    company_abbr = frappe.db.get_value("Company", company, "abbr")
    warehouse_name = f"Van - {doc.vehicle_number}"

    # Check if warehouse already exists
    existing = frappe.db.exists("Warehouse", {"warehouse_name": warehouse_name})
    if existing:
        doc.warehouse = existing
        doc.db_set("warehouse", existing)
        return

    # Create new warehouse
    warehouse = frappe.get_doc({
        "doctype": "Warehouse",
        "warehouse_name": warehouse_name,
        "company": company,
        "is_group": 0,
        "parent_warehouse": f"All Warehouses - {company_abbr}",
    })
    warehouse.insert(ignore_permissions=True)

    doc.warehouse = warehouse.name
    doc.db_set("warehouse", warehouse.name)

    frappe.msgprint(
        f"Warehouse '{warehouse.name}' created for vehicle {doc.vehicle_number}",
        indicator="green",
        alert=True
    )


@frappe.whitelist()
def get_vehicle_stock(vehicle):
    """Get current stock in vehicle warehouse"""
    warehouse = frappe.db.get_value("Vehicle", vehicle, "warehouse")
    if not warehouse:
        return []

    return frappe.db.sql("""
        SELECT
            item_code,
            item_name,
            actual_qty,
            stock_uom
        FROM `tabBin`
        WHERE warehouse = %s
        AND actual_qty > 0
        ORDER BY item_code
    """, warehouse, as_dict=True)
