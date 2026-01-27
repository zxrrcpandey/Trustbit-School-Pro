# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class BookSampleCollection(Document):
    def validate(self):
        self.validate_items()
        self.validate_distribution_reference()
        self.validate_quantities()
        self.calculate_totals()

    def validate_items(self):
        """Validate that items are provided"""
        if not self.items:
            frappe.throw(_("Please add at least one book to collect"))

    def validate_distribution_reference(self):
        """Validate distribution reference and fetch school"""
        if self.distribution_reference:
            dist = frappe.get_doc("Book Sample Distribution", self.distribution_reference)
            if dist.docstatus != 1:
                frappe.throw(_("Distribution {0} is not submitted").format(self.distribution_reference))

            if not self.school:
                self.school = dist.school

            if self.school != dist.school:
                frappe.throw(_("School does not match with distribution reference"))

    def validate_quantities(self):
        """Validate collection quantities don't exceed pending"""
        for item in self.items:
            total_collection = flt(item.qty_collected) + flt(item.qty_damaged) + flt(item.qty_lost)

            if total_collection > flt(item.qty_pending):
                frappe.throw(
                    _("Total collection ({0}) cannot exceed pending quantity ({1}) for {2}").format(
                        total_collection, item.qty_pending, item.item_code
                    )
                )

            if flt(item.qty_collected) < 0 or flt(item.qty_damaged) < 0 or flt(item.qty_lost) < 0:
                frappe.throw(_("Quantities cannot be negative for {0}").format(item.item_code))

    def calculate_totals(self):
        """Calculate total quantities"""
        self.total_qty_collected = sum(flt(item.qty_collected) for item in self.items)
        self.total_qty_damaged = sum(flt(item.qty_damaged) for item in self.items)
        self.total_qty_lost = sum(flt(item.qty_lost) for item in self.items)

    def on_submit(self):
        """Create stock entries and update distribution on submit"""
        self.create_stock_entries()
        self.update_distribution()
        self.db_set("status", "Collected")

    def on_cancel(self):
        """Cancel linked stock entries and revert distribution"""
        self.cancel_stock_entries()
        self.revert_distribution()
        self.db_set("status", "Cancelled")

    def create_stock_entries(self):
        """Create Stock Entries for collection"""
        # Stock Entry for good collected books (Material Transfer back to main warehouse)
        collected_items = [item for item in self.items if flt(item.qty_collected) > 0]
        if collected_items:
            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Transfer"
            se.posting_date = self.collection_date
            se.from_warehouse = self.source_warehouse
            se.to_warehouse = self.target_warehouse
            se.custom_book_sample_collection = self.name

            for item in collected_items:
                se.append("items", {
                    "item_code": item.item_code,
                    "qty": item.qty_collected,
                    "s_warehouse": self.source_warehouse,
                    "t_warehouse": self.target_warehouse,
                })

            se.insert()
            se.submit()
            self.db_set("stock_entry", se.name)

            frappe.msgprint(
                _("Stock Entry {0} created for collected books").format(
                    f'<a href="/app/stock-entry/{se.name}">{se.name}</a>'
                ),
                indicator="green",
                alert=True
            )

        # Stock Entry for damaged/lost books (Material Issue - write off)
        damaged_items = [item for item in self.items if flt(item.qty_damaged) + flt(item.qty_lost) > 0]
        if damaged_items:
            se_damaged = frappe.new_doc("Stock Entry")
            se_damaged.stock_entry_type = "Material Issue"
            se_damaged.posting_date = self.collection_date
            se_damaged.custom_book_sample_collection = self.name

            for item in damaged_items:
                write_off_qty = flt(item.qty_damaged) + flt(item.qty_lost)
                if write_off_qty > 0:
                    se_damaged.append("items", {
                        "item_code": item.item_code,
                        "qty": write_off_qty,
                        "s_warehouse": self.source_warehouse,
                    })

            se_damaged.insert()
            se_damaged.submit()
            self.db_set("stock_entry_damaged", se_damaged.name)

            frappe.msgprint(
                _("Stock Entry {0} created for damaged/lost books").format(
                    f'<a href="/app/stock-entry/{se_damaged.name}">{se_damaged.name}</a>'
                ),
                indicator="orange",
                alert=True
            )

    def cancel_stock_entries(self):
        """Cancel linked stock entries"""
        if self.stock_entry:
            se = frappe.get_doc("Stock Entry", self.stock_entry)
            if se.docstatus == 1:
                se.cancel()

        if self.stock_entry_damaged:
            se_damaged = frappe.get_doc("Stock Entry", self.stock_entry_damaged)
            if se_damaged.docstatus == 1:
                se_damaged.cancel()

    def update_distribution(self):
        """Update collection quantities in distribution"""
        if not self.distribution_reference:
            return

        dist = frappe.get_doc("Book Sample Distribution", self.distribution_reference)

        collection_data = []
        for item in self.items:
            collection_data.append({
                "item_code": item.item_code,
                "qty_collected": flt(item.qty_collected) + flt(item.qty_damaged) + flt(item.qty_lost),
            })

        dist.update_collection(collection_data)

    def revert_distribution(self):
        """Revert collection quantities in distribution on cancel"""
        if not self.distribution_reference:
            return

        dist = frappe.get_doc("Book Sample Distribution", self.distribution_reference)

        # Negative collection to revert
        collection_data = []
        for item in self.items:
            collection_data.append({
                "item_code": item.item_code,
                "qty_collected": -(flt(item.qty_collected) + flt(item.qty_damaged) + flt(item.qty_lost)),
            })

        dist.update_collection(collection_data)


@frappe.whitelist()
def get_items_from_distribution(distribution):
    """Get pending items from a distribution for collection"""
    from trustbit_school_pro.trustbit_school_pro.doctype.book_sample_distribution.book_sample_distribution import (
        get_pending_items_for_collection,
    )
    return get_pending_items_for_collection(distribution)


@frappe.whitelist()
def make_collection_from_distribution(distribution):
    """Create a new Book Sample Collection from Distribution"""
    dist = frappe.get_doc("Book Sample Distribution", distribution)

    if dist.docstatus != 1:
        frappe.throw(_("Distribution must be submitted"))

    if dist.status == "Fully Collected":
        frappe.throw(_("All samples have already been collected"))

    collection = frappe.new_doc("Book Sample Collection")
    collection.school = dist.school
    collection.distribution_reference = dist.name
    collection.source_warehouse = dist.target_warehouse  # Samples in Field

    # Add pending items
    for item in dist.items:
        if flt(item.qty_pending) > 0:
            collection.append("items", {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "class_grade": item.class_grade,
                "qty_distributed": item.qty,
                "qty_previously_collected": item.qty_collected,
                "qty_pending": item.qty_pending,
                "qty_collected": item.qty_pending,  # Default to full collection
            })

    return collection
