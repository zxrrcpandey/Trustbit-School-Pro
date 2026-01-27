import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    """Run after app installation"""
    create_item_custom_fields()
    create_sample_warehouse()
    frappe.db.commit()


def create_item_custom_fields():
    """Create custom fields for Item master"""
    custom_fields = {
        "Item": [
            {
                "fieldname": "book_sample_section",
                "label": "Book Sample Details",
                "fieldtype": "Section Break",
                "insert_after": "description",
                "collapsible": 1,
                "depends_on": "eval:doc.custom_is_sample_book",
            },
            {
                "fieldname": "custom_is_sample_book",
                "label": "Is Sample Book",
                "fieldtype": "Check",
                "insert_after": "item_group",
                "description": "Check if this item is a book used for sampling to schools",
            },
            {
                "fieldname": "custom_subject",
                "label": "Subject",
                "fieldtype": "Data",
                "insert_after": "book_sample_section",
                "depends_on": "eval:doc.custom_is_sample_book",
            },
            {
                "fieldname": "custom_class_grade",
                "label": "Class/Grade",
                "fieldtype": "Data",
                "insert_after": "custom_subject",
                "depends_on": "eval:doc.custom_is_sample_book",
                "description": "Class 1, 2, 3... 12",
            },
            {
                "fieldname": "custom_column_break_book",
                "fieldtype": "Column Break",
                "insert_after": "custom_class_grade",
            },
            {
                "fieldname": "custom_author",
                "label": "Author",
                "fieldtype": "Data",
                "insert_after": "custom_column_break_book",
                "depends_on": "eval:doc.custom_is_sample_book",
            },
            {
                "fieldname": "custom_edition_year",
                "label": "Edition/Year",
                "fieldtype": "Data",
                "insert_after": "custom_author",
                "depends_on": "eval:doc.custom_is_sample_book",
            },
            {
                "fieldname": "custom_isbn",
                "label": "ISBN",
                "fieldtype": "Data",
                "insert_after": "custom_edition_year",
                "depends_on": "eval:doc.custom_is_sample_book",
                "unique": 1,
            },
            {
                "fieldname": "custom_publisher",
                "label": "Publisher",
                "fieldtype": "Link",
                "options": "Supplier",
                "insert_after": "custom_isbn",
                "depends_on": "eval:doc.custom_is_sample_book",
            },
        ]
    }
    create_custom_fields(custom_fields, update=True)
    frappe.msgprint("Custom fields for Item master created successfully!")


def create_sample_warehouse():
    """Create default 'Samples in Field' warehouse"""
    if not frappe.db.exists("Warehouse", {"warehouse_name": "Samples in Field"}):
        # Get default company
        company = frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            company = frappe.db.get_value("Company", {}, "name")

        if company:
            warehouse = frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": "Samples in Field",
                "company": company,
                "is_group": 0,
                "parent_warehouse": f"All Warehouses - {frappe.db.get_value('Company', company, 'abbr')}",
            })
            warehouse.insert(ignore_permissions=True)
            frappe.msgprint(f"'Samples in Field' warehouse created for {company}")
