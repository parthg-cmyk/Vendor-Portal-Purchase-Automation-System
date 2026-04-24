import frappe
import unittest
from frappe.exceptions import ValidationError
from frappe.model.workflow import apply_workflow
import random

class TestVendorOnboarding(unittest.TestCase):

    def setUp(self):
        self.settings = frappe.get_single("Vendor Portal Settings")
        self.settings.min_documents_required = 2
        self.settings.save()


    def get_valid_doc(self):
        unique = frappe.generate_hash(length=5)

        return frappe.get_doc({
            "doctype": "Vendor Onboarding",
            "supplier_name": f"Test Vendor {unique}",
            "company_name": "Test Company Pvt Ltd",
            "email": f"test{unique}@example.com",
            "phone": "9876543210",
            "gst_number": f"22AAAAA{random.randint(1000,9999)}A1Z5",
            "pan_number": f"AAAAA{random.randint(1000,9999)}A",
            "vendor_category": "Raw Materials",
            "address_line_1": "Test Address",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "documents": [
                {"document_name": "Doc1", "document_file": "/files/test1.pdf"},
                {"document_name": "Doc2", "document_file": "/files/test2.pdf"},
            ],
        })

    # ✅ GST Validation
    def test_gst_validation_format(self):
        doc = self.get_valid_doc()
        doc.gst_number = "INVALIDGST"

        self.assertRaises(ValidationError, doc.insert)

    # ✅ PAN Validation
    def test_pan_validation_format(self):
        doc = self.get_valid_doc()
        doc.pan_number = "INVALIDPAN"

        self.assertRaises(ValidationError, doc.insert)

    # ✅ Minimum Documents
    def test_minimum_documents_required(self):
        doc = self.get_valid_doc()

        # Replace properly BEFORE insert
        doc.set("documents", [
            {
                "document_name": "Only One",
                "document_file": "/files/test1.pdf"
            }
        ])

        self.assertRaises(ValidationError, doc.insert)

    # ✅ Approve creates Supplier
    def test_approve_creates_supplier(self):
        doc = self.get_valid_doc()
        doc.insert()

        doc.onboarding_status = "Under Review"
        doc.save()

        doc.onboarding_status = "Approved"
        doc.save()

        supplier = frappe.db.exists("Supplier", {"supplier_name": doc.supplier_name})
        self.assertTrue(supplier)

    # ✅ Reject sets reason
    def test_reject_sets_reason(self):
        doc = self.get_valid_doc()
        doc.insert()

        # Move through workflow properly
        apply_workflow(doc, "Submit For Review")

        # Set rejection reason BEFORE rejection
        doc.rejection_reason = "Invalid docs"
        doc.save()

        # Reject via workflow
        apply_workflow(doc, "Reject")

        # Fetch fresh doc from DB
        updated_doc = frappe.get_doc("Vendor Onboarding", doc.name)

        self.assertEqual(updated_doc.onboarding_status, "Rejected")
        self.assertEqual(updated_doc.rejection_reason, "Invalid docs")

    # ✅ Duplicate GST blocked
    def test_duplicate_gst_blocked(self):
        gst = "22AAAAA9999A1Z5"  # fixed GST for this test

        doc1 = self.get_valid_doc()
        doc1.gst_number = gst
        doc1.insert()

        doc1.onboarding_status = "Under Review"
        doc1.save()

        doc1.onboarding_status = "Approved"
        doc1.save()

        doc2 = self.get_valid_doc()
        doc2.gst_number = gst  # same GST
        doc2.supplier_name = "Another Vendor"

        self.assertRaises(ValidationError, doc2.insert)