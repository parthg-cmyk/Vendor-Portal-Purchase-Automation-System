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
        if self.email:
            frappe.utils.validate_email_address(self.email, throw=True)

    def validate_minimum_documents(self):
        settings = frappe.get_single("Vendor Portal Settings")

        if settings.min_documents_required > len(self.documents):
                frappe.throw(_(f"Minimum {settings.min_documents_required} Documents Required"))

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

