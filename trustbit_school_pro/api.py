# Trustbit School Pro - API Functions

import frappe


@frappe.whitelist()
def get_item_by_barcode(barcode):
    """
    Get item code by barcode.
    Searches in the Item Barcode child table.
    """
    if not barcode:
        return None

    # Search in Item Barcode table
    item_barcode = frappe.db.get_value(
        "Item Barcode",
        {"barcode": barcode},
        "parent"
    )

    if item_barcode:
        return item_barcode

    # Also try searching by item_code directly (in case barcode matches item code)
    if frappe.db.exists("Item", barcode):
        return barcode

    return None
