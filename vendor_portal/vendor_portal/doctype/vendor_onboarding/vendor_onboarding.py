import re
import frappe
from frappe.model.document import Document
from frappe import _


class VendorOnboarding(Document):

    def validate(self):
        self.validate_gst()
        self.validate_pan()
        self.validate_email()
        self.validate_minimum_documents()
        self.check_duplicate_gst()

    def validate_gst(self):
        if not self.gst_number:
            return

        gst_regex = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        if not re.match(gst_regex, self.gst_number):
            frappe.throw(_("Invalid GST Number format"))

    def validate_pan(self):
        if not self.pan_number:
            return

        pan_regex = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
        if not re.match(pan_regex, self.pan_number):
            frappe.throw(_("Invalid PAN format"))

    def validate_email(self):
        if self.email_id:
            frappe.utils.validate_email_address(self.email_id, throw=True)

    def validate_minimum_documents(self):
        settings = frappe.get_single("Vendor Portal Settings")

        if settings.required_documents:
            uploaded_docs = [d.document_type for d in self.documents]

            for doc in settings.required_documents:
                if doc.document_type not in uploaded_docs:
                    frappe.throw(_(f"Missing required document: {doc.document_type}"))

    def check_duplicate_gst(self):
        if not self.gst_number:
            return

        # Check approved onboarding
        onboarding = frappe.db.exists(
            "Vendor Onboarding",
            {
                "gst_number": self.gst_number,
                "onboarding_status": "Approved",
                "name": ["!=", self.name],
            },
        )

        # Check active supplier
        supplier = frappe.db.exists("Supplier", {"gstin": self.gst_number})

        if onboarding or supplier:
            frappe.throw(_("Vendor with this GST already exists"))

    def on_submit(self):
        self.onboarding_status = "Under Review"


@frappe.whitelist()
def approve_onboarding(onboarding_name):

    # Permission check
    if "Purchase Manager" not in frappe.get_roles():
        frappe.throw("Only Purchase Manager can approve onboarding")

    doc = frappe.get_doc("Vendor Onboarding", onboarding_name)

    if doc.onboarding_status == "Approved":
        frappe.throw("Already approved")

    settings = frappe.get_single("Vendor Portal Settings")

    # Create Supplier
    supplier = frappe.get_doc(
        {
            "doctype": "Supplier",
            "supplier_name": doc.vendor_name,
            "supplier_group": settings.default_supplier_group,
            "vendor_category": doc.vendor_category,
            "gstin": doc.gst_number,
            "pan": doc.pan_number,
        }
    )

    supplier.insert(ignore_permissions=True)

    # Create Address
    if doc.address_line1:
        address = frappe.get_doc(
            {
                "doctype": "Address",
                "address_title": doc.vendor_name,
                "address_line1": doc.address_line1,
                "city": doc.city,
                "state": doc.state,
                "pincode": doc.pincode,
                "country": doc.country,
                "links": [{"link_doctype": "Supplier", "link_name": supplier.name}],
            }
        )
        address.insert(ignore_permissions=True)

    # Create Contact
    if doc.email_id or doc.phone:
        contact = frappe.get_doc(
            {
                "doctype": "Contact",
                "first_name": doc.vendor_name,
                "email_id": doc.email_id,
                "phone": doc.phone,
                "links": [{"link_doctype": "Supplier", "link_name": supplier.name}],
            }
        )
        contact.insert(ignore_permissions=True)

    # Bank Details (if you have custom doctype or fields)
    if doc.bank_account:
        bank = frappe.get_doc(
            {
                "doctype": "Bank Account",
                "party_type": "Supplier",
                "party": supplier.name,
                "bank_account_no": doc.bank_account,
                "ifsc": doc.ifsc_code,
            }
        )
        bank.insert(ignore_permissions=True)

    # Update onboarding
    doc.onboarding_status = "Approved"
    doc.linked_supplier = supplier.name
    doc.save(ignore_permissions=True)

    # Send Email
    if doc.email_id:
        frappe.sendmail(
            recipients=[doc.email_id],
            subject="Vendor Approved",
            message=f"Hello {doc.vendor_name}, your onboarding is approved.",
        )

    return supplier.name


@frappe.whitelist()
def reject_onboarding(onboarding_name, reason):

    if "Purchase Manager" not in frappe.get_roles():
        frappe.throw("Only Purchase Manager can reject onboarding")

    doc = frappe.get_doc("Vendor Onboarding", onboarding_name)

    doc.onboarding_status = "Rejected"
    doc.rejection_reason = reason
    doc.save(ignore_permissions=True)

    # Optional email
    if doc.email_id:
        frappe.sendmail(
            recipients=[doc.email_id],
            subject="Vendor Rejected",
            message=f"Your onboarding is rejected. Reason: {reason}",
        )
