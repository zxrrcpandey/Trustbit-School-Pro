# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class BookSampleDistribution(Document):
    def validate(self):
        self.validate_items()
        self.validate_warehouse()
        self.set_expected_return_dates()
        self.calculate_totals()
        self.validate_stock_availability()
        self.update_item_collection_status()

    def validate_items(self):
        """Validate that items are provided"""
        if not self.items:
            frappe.throw(_("Please add at least one book to distribute"))

        for item in self.items:
            if flt(item.qty) <= 0:
                frappe.throw(_("Quantity must be greater than 0 for {0}").format(item.item_code))

    def validate_warehouse(self):
        """Validate source and target warehouses"""
        if self.source_warehouse == self.target_warehouse:
            frappe.throw(_("Source and Target warehouse cannot be the same"))

        # If loading reference is provided, use its vehicle's warehouse
        if self.loading_reference and not self.source_warehouse:
            vehicle = frappe.db.get_value("Book Sample Loading", self.loading_reference, "vehicle")
            if vehicle:
                self.source_warehouse = frappe.db.get_value("Vehicle", vehicle, "warehouse")
                self.vehicle = vehicle

    def set_expected_return_dates(self):
        """Set expected return date on items if not set"""
        if self.expected_return_date:
            for item in self.items:
                if not item.expected_return_date:
                    item.expected_return_date = self.expected_return_date

    def calculate_totals(self):
        """Calculate total quantities"""
        self.total_qty_distributed = sum(flt(item.qty) for item in self.items)
        self.total_qty_collected = sum(flt(item.qty_collected) for item in self.items)
        self.total_qty_pending = self.total_qty_distributed - self.total_qty_collected

    def validate_stock_availability(self):
        """Check if stock is available in source warehouse"""
        for item in self.items:
            available_qty = get_stock_balance(item.item_code, self.source_warehouse)
            item.available_qty_in_van = available_qty

            if self.docstatus == 0 and flt(available_qty) < flt(item.qty):
                frappe.msgprint(
                    _("Insufficient stock for {0}. Available: {1}, Required: {2}").format(
                        item.item_code, available_qty, item.qty
                    ),
                    indicator="orange",
                    alert=True
                )

    def update_item_collection_status(self):
        """Update collection status for each item"""
        for item in self.items:
            item.qty_pending = flt(item.qty) - flt(item.qty_collected)

            if flt(item.qty_collected) <= 0:
                item.collection_status = "Pending"
            elif flt(item.qty_collected) >= flt(item.qty):
                item.collection_status = "Collected"
            else:
                item.collection_status = "Partial"

    def update_status(self):
        """Update overall distribution status based on collection"""
        if self.docstatus == 2:
            self.status = "Cancelled"
        elif self.docstatus == 0:
            self.status = "Draft"
        else:
            if flt(self.total_qty_pending) <= 0:
                self.status = "Fully Collected"
            elif flt(self.total_qty_collected) > 0:
                self.status = "Partially Collected"
            else:
                self.status = "Distributed"

    def on_submit(self):
        """Create stock entry on submit"""
        self.create_stock_entry()
        self.db_set("status", "Distributed")

    def on_cancel(self):
        """Cancel linked stock entry"""
        if self.stock_entry:
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                se.cancel()
        self.db_set("status", "Cancelled")

    def create_stock_entry(self):
        """Create Material Transfer Stock Entry to 'Samples in Field'"""
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Transfer"
        se.posting_date = self.distribution_date
        se.from_warehouse = self.source_warehouse
        se.to_warehouse = self.target_warehouse
        se.custom_book_sample_distribution = self.name

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
    def update_collection(self, items):
        """Update collection quantities from collection document"""
        if self.docstatus != 1:
            frappe.throw(_("Document must be submitted to update collection"))

        for collection_item in items:
            for item in self.items:
                if item.item_code == collection_item.get("item_code"):
                    item.qty_collected = flt(item.qty_collected) + flt(collection_item.get("qty_collected", 0))
                    item.qty_pending = flt(item.qty) - flt(item.qty_collected)

                    if flt(item.qty_collected) >= flt(item.qty):
                        item.collection_status = "Collected"
                    elif flt(item.qty_collected) > 0:
                        item.collection_status = "Partial"

        self.calculate_totals()
        self.update_status()
        self.save(ignore_permissions=True)


def get_stock_balance(item_code, warehouse):
    """Get actual stock balance for an item in warehouse"""
    return flt(frappe.db.get_value(
        "Bin",
        {"item_code": item_code, "warehouse": warehouse},
        "actual_qty"
    ))


@frappe.whitelist()
def get_pending_items_for_collection(distribution):
    """Get pending items for collection from a distribution"""
    doc = frappe.get_doc("Book Sample Distribution", distribution)

    pending_items = []
    for item in doc.items:
        if flt(item.qty_pending) > 0:
            pending_items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "class_grade": item.class_grade,
                "subject": item.subject,
                "qty_distributed": item.qty,
                "qty_collected": item.qty_collected,
                "qty_pending": item.qty_pending,
                "expected_return_date": item.expected_return_date,
            })

    return pending_items


@frappe.whitelist()
def get_pending_distributions_for_school(school):
    """Get all pending distributions for a school"""
    return frappe.db.sql("""
        SELECT
            bsd.name,
            bsd.distribution_date,
            bsd.distributor_name,
            bsd.total_qty_distributed,
            bsd.total_qty_collected,
            bsd.total_qty_pending,
            bsd.expected_return_date
        FROM `tabBook Sample Distribution` bsd
        WHERE bsd.school = %s
        AND bsd.docstatus = 1
        AND bsd.status IN ('Distributed', 'Partially Collected')
        ORDER BY bsd.distribution_date
    """, school, as_dict=True)
