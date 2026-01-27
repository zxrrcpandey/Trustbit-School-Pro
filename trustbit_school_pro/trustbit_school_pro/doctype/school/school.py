# Copyright (c) 2024, Trustbit Software and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class School(Document):
    def validate(self):
        self.validate_contact()

    def validate_contact(self):
        """Validate at least one contact method is provided"""
        if not self.phone and not self.mobile and not self.email:
            frappe.msgprint(
                "It is recommended to provide at least one contact method (Phone, Mobile, or Email)",
                indicator="orange",
                alert=True
            )

    def before_save(self):
        """Auto-create Customer if not linked"""
        pass  # Customer creation is optional, user can link manually

    @frappe.whitelist()
    def create_customer(self):
        """Create a Customer from this School"""
        if self.customer:
            frappe.throw("Customer already linked to this school")

        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": self.school_name,
            "customer_type": "Company",
            "customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups",
            "territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
        })
        customer.insert(ignore_permissions=True)

        self.customer = customer.name
        self.save()

        frappe.msgprint(f"Customer '{customer.name}' created and linked successfully!")
        return customer.name


@frappe.whitelist()
def get_pending_samples(school):
    """Get pending sample books for a school"""
    return frappe.db.sql("""
        SELECT
            bsd.name as distribution,
            bsdi.item_code,
            bsdi.item_name,
            bsdi.class_grade,
            bsdi.qty as qty_distributed,
            COALESCE(bsdi.qty_collected, 0) as qty_collected,
            (bsdi.qty - COALESCE(bsdi.qty_collected, 0)) as qty_pending,
            bsd.distribution_date,
            bsd.expected_return_date
        FROM `tabBook Sample Distribution` bsd
        INNER JOIN `tabBook Sample Distribution Item` bsdi ON bsdi.parent = bsd.name
        WHERE bsd.school = %s
        AND bsd.docstatus = 1
        AND (bsdi.qty - COALESCE(bsdi.qty_collected, 0)) > 0
        ORDER BY bsd.distribution_date
    """, school, as_dict=True)
