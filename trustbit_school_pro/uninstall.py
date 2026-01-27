import frappe


def before_uninstall():
    """Clean up before uninstalling the app"""
    # Remove custom fields
    custom_fields = frappe.get_all(
        "Custom Field",
        filters={"module": "Trustbit School Pro"},
        pluck="name"
    )
    for field in custom_fields:
        frappe.delete_doc("Custom Field", field, force=True)

    frappe.db.commit()
