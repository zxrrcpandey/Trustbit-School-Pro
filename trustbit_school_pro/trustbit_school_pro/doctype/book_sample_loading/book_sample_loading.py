# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BookSampleLoading(Document):
    def validate(self):
        self.validate_items()
        self.validate_warehouse()
        self.calculate_total_qty()
        self.validate_stock_availability()

    def validate_items(self):
        """Validate that items are provided"""
        if not self.items:
            frappe.throw(_("Please add at least one book to load"))

        for item in self.items:
            if flt(item.qty) <= 0:
                frappe.throw(_("Quantity must be greater than 0 for {0}").format(item.item_code))

    def validate_warehouse(self):
        """Validate source and target warehouses"""
        if not self.target_warehouse:
            # Fetch from vehicle if not set
            self.target_warehouse = frappe.db.get_value("Vehicle", self.vehicle, "warehouse")

        if not self.target_warehouse:
            frappe.throw(_("Vehicle {0} does not have a warehouse assigned").format(self.vehicle))

        if self.source_warehouse == self.target_warehouse:
            frappe.throw(_("Source and Target warehouse cannot be the same"))

    def calculate_total_qty(self):
        """Calculate total quantity"""
        self.total_qty = sum(flt(item.qty) for item in self.items)

    def validate_stock_availability(self):
        """Check if stock is available in source warehouse"""
        for item in self.items:
            available_qty = get_stock_balance(item.item_code, self.source_warehouse)
            item.available_qty = available_qty

            if flt(available_qty) < flt(item.qty):
                frappe.msgprint(
                    _("Insufficient stock for {0}. Available: {1}, Required: {2}").format(
                        item.item_code, available_qty, item.qty
                    ),
                    indicator="orange",
                    alert=True
                )

    def on_submit(self):
        """Create stock entry on submit"""
        self.create_stock_entry()
        self.db_set("status", "Loaded")

    def on_cancel(self):
        """Cancel linked stock entry"""
        if self.stock_entry:
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                se.cancel()
        self.db_set("status", "Cancelled")

    def create_stock_entry(self):
        """Create Material Transfer Stock Entry"""
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Transfer"
        se.posting_date = self.loading_date
        se.from_warehouse = self.source_warehouse
        se.to_warehouse = self.target_warehouse
        se.custom_book_sample_loading = self.name

        for item in self.items:
            se.append("items", {
                "item_code": item.item_code,
                "qty": item.qty,
                "s_warehouse": self.source_warehouse,
                "t_warehouse": self.target_warehouse,
            })

        se.insert()
        se.submit()

        self.db_set("stock_entry", se.name)
        frappe.msgprint(
            _("Stock Entry {0} created").format(
                f'<a href="/app/stock-entry/{se.name}">{se.name}</a>'
            ),
            indicator="green",
            alert=True
        )

    @frappe.whitelist()
    def update_status(self, status):
        """Update loading status"""
        if self.docstatus != 1:
            frappe.throw(_("Document must be submitted to update status"))

        valid_statuses = ["Loaded", "In Transit", "Returned"]
        if status not in valid_statuses:
            frappe.throw(_("Invalid status. Must be one of: {0}").format(", ".join(valid_statuses)))

        self.db_set("status", status)
        return status


def get_stock_balance(item_code, warehouse):
    """Get actual stock balance for an item in warehouse"""
    return flt(frappe.db.get_value(
        "Bin",
        {"item_code": item_code, "warehouse": warehouse},
        "actual_qty"
    ))


@frappe.whitelist()
def get_stock_balance_api(item_code, warehouse):
    """API to get stock balance - called from client script"""
    return get_stock_balance(item_code, warehouse)


@frappe.whitelist()
def get_items_for_vehicle(vehicle):
    """Get current stock items in vehicle warehouse"""
    warehouse = frappe.db.get_value("Vehicle", vehicle, "warehouse")
    if not warehouse:
        return []

    items = frappe.db.sql("""
        SELECT
            b.item_code,
            i.item_name,
            i.custom_subject as subject,
            b.actual_qty as available_qty,
            i.stock_uom
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE b.warehouse = %s
        AND b.actual_qty > 0
        ORDER BY i.item_name
    """, warehouse, as_dict=True)

    # Fetch class grades for each item
    for item in items:
        item['class_grade'] = get_item_class_grades(item['item_code'])

    return items


@frappe.whitelist()
def get_item_class_grades(item_code):
    """Get class grades for an item as comma-separated string"""
    class_grades = frappe.db.get_all(
        "Item Class Grade",
        filters={"parent": item_code, "parenttype": "Item"},
        fields=["class_grade"],
        order_by="idx"
    )
    return ", ".join([cg.class_grade for cg in class_grades]) if class_grades else ""
