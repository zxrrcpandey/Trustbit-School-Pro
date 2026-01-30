import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    """Run after app installation"""
    create_default_class_grades()
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
                "fieldname": "custom_class_grades",
                "label": "Class/Grades",
                "fieldtype": "Table MultiSelect",
                "options": "Item Class Grade",
                "insert_after": "custom_subject",
                "depends_on": "eval:doc.custom_is_sample_book",
                "description": "Select one or more classes this book is for",
            },
            {
                "fieldname": "custom_column_break_book",
                "fieldtype": "Column Break",
                "insert_after": "custom_class_grades",
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


def create_default_class_grades():
    """Create default class grades"""
    default_grades = [
        {"class_name": "Nursery", "class_order": -3},
        {"class_name": "LKG", "class_order": -2},
        {"class_name": "UKG", "class_order": -1},
        {"class_name": "Class 1", "class_order": 1},
        {"class_name": "Class 2", "class_order": 2},
        {"class_name": "Class 3", "class_order": 3},
        {"class_name": "Class 4", "class_order": 4},
        {"class_name": "Class 5", "class_order": 5},
        {"class_name": "Class 6", "class_order": 6},
        {"class_name": "Class 7", "class_order": 7},
        {"class_name": "Class 8", "class_order": 8},
        {"class_name": "Class 9", "class_order": 9},
        {"class_name": "Class 10", "class_order": 10},
        {"class_name": "Class 11", "class_order": 11},
        {"class_name": "Class 12", "class_order": 12},
    ]

    created_count = 0
    for grade in default_grades:
        if not frappe.db.exists("Class Grade", grade["class_name"]):
            doc = frappe.get_doc({
                "doctype": "Class Grade",
                "class_name": grade["class_name"],
                "class_order": grade["class_order"],
                "is_active": 1
            })
            doc.insert(ignore_permissions=True)
            created_count += 1

    if created_count > 0:
        frappe.msgprint(f"{created_count} default Class Grades created successfully!")
