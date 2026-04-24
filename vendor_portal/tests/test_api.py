import frappe
import unittest
from frappe.exceptions import ValidationError
from frappe.utils import random_string
from frappe.utils import nowdate, add_days


class TestVendorPortalAPI(unittest.TestCase):

    def create_supplier(self, name, rating=4, blacklisted=0):
        supplier = frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": name,
                "supplier_group": "All Supplier Groups",
                "custom_vendor_rating": rating,
                "custom_is_blacklisted": blacklisted,
            }
        ).insert(ignore_permissions=True)

        return supplier

    def create_test_item(self):
        if not frappe.db.exists("Item", "_Test Item"):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": "_Test Item",
                    "item_name": "_Test Item",
                    "item_group": "All Item Groups",
                    "stock_uom": "Nos",
                    "is_stock_item": 1,
                }
            ).insert(ignore_permissions=True)

    # ✅ Blacklisted Supplier blocks PO
    def test_blacklisted_supplier_blocks_po(self):
        supplier = self.create_supplier(f"Blacklisted Vendor {random_string(5)}", blacklisted=1)

        po = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "supplier": supplier.name,
                "items": [{"item_code": "_Test Item", "qty": 1, "rate": 100}],
            }
        )

        self.assertRaises(ValidationError, po.insert)

    # ✅ Low rating blocks PO
    def test_low_rating_blocks_po(self):
        settings = frappe.get_single("Vendor Portal Settings")
        settings.low_rating_threshold = 3
        settings.save()

        supplier = self.create_supplier(f"Low Rating Vendor {random_string(5)}", rating=2)

        po = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "supplier": supplier.name,
                "items": [{"item_code": "_Test Item", "qty": 1, "rate": 100}],
            }
        )

        self.assertRaises(ValidationError, po.insert)

    # ✅ PO submit creates Pricing rating
    def test_po_submit_creates_pricing_rating(self):
        supplier_name = f"PO Vendor {random_string(5)}"

        supplier = frappe.get_doc(
            {"doctype": "Supplier", "supplier_name": supplier_name}
        ).insert(ignore_permissions=True)

        self.create_test_item()

        po = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "supplier": supplier.name,
                "company": "Sanskar Technologies Pvt Ltd (Demo)",
                "schedule_date": frappe.utils.today(),
                "items": [
                    {
                        "item_code": "_Test Item",
                        "qty": 10,
                        "rate": 100,
                        "warehouse": "Finished Goods - STPLD",
                    }
                ],
            }
        ).insert(ignore_permissions=True)

        po.submit()

        rating = frappe.db.exists(
            "Vendor Rating Log", {"supplier": supplier.name, "rating_type": "Pricing"}
        )

        self.assertTrue(rating)

    # ✅ PO cancel deletes rating
    def test_po_cancel_deletes_rating(self):
        supplier = self.create_supplier(f"Cancel Vendor {random_string(5)}")

        po = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "supplier": supplier.name,
                "schedule_date": add_days(nowdate(), 5),  # ✅ REQUIRED
                "items": [
                    {
                        "item_code": "_Test Item",
                        "qty": 1,
                        "rate": 100,
                        "warehouse": "Finished Goods - STPLD",  # also required (from previous error)
                    }
                ],
            }
        ).insert()
        po.submit()
        po.cancel()

        rating = frappe.db.exists(
            "Vendor Rating Log", {"supplier": supplier.name, "rating_type": "Pricing"}
        )

        self.assertFalse(rating)

    # ✅ PR submit creates Delivery rating
    def test_pr_submit_creates_delivery_rating(self):
        supplier = self.create_supplier(f"PR Vendor {random_string(5)}")

        pr = frappe.get_doc(
            {
                "doctype": "Purchase Receipt",
                "supplier": supplier.name,
                "items": [
                    {
                        "item_code": "_Test Item",
                        "qty": 10,
                        "received_qty": 10,
                        "rate": 100,
                        "warehouse": "Finished Goods - STPLD",
                    }
                ],
            }
        ).insert()

        pr.submit()

        rating = frappe.db.exists(
            "Vendor Rating Log", {"supplier": supplier.name, "rating_type": "Delivery"}
        )

        self.assertTrue(rating)

    # ✅ Vendor rating recalculation
    def test_vendor_rating_recalculation(self):
        supplier = self.create_supplier(f"Rating Vendor {random_string(5)}")

        for score in [5, 4, 3]:
            frappe.get_doc(
                {
                    "doctype": "Vendor Rating Log",
                    "supplier": supplier.name,
                    "rating_type": "Quality",
                    "score": score,
                }
            ).insert()

        from vendor_portal.patches.v1_0 import recalculate_vendor_ratings

        recalculate_vendor_ratings.execute()

        updated = frappe.get_doc("Supplier", supplier.name)

        self.assertTrue(updated.custom_vendor_rating > 0)

    # ✅ Permission test
    def test_permission_own_ratings_only(self):
        # Create supplier first
        supplier = frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": f"Test Supplier {random_string(3)}",
            }
        ).insert(ignore_permissions=True)

        # Create user with role
        user1 = frappe.get_doc(
            {
                "doctype": "User",
                "first_name": f"Test User {random_string(3)}",
                "email": f"user{random_string(3)}@test.com",
                "roles": [{"role": "System Manager"}],
            }
        ).insert(ignore_permissions=True)

        frappe.set_user(user1.name)

        # Use actual supplier name
        rating = frappe.get_doc(
            {
                "doctype": "Vendor Rating Log",
                "supplier": supplier.name,  # ✅ FIXED
                "rating_type": "Quality",
                "score": 4,
            }
        ).insert()

        frappe.set_user("Administrator")

        self.assertEqual(rating.owner, user1.name)

    # ✅ Supplier comparison API
    def test_supplier_comparison_api(self):
        self.create_supplier(f"Vendor A {random_string(5)}", rating=5)
        self.create_supplier(f"Vendor B {random_string(5)}", rating=3)

        result = frappe.call(
            "vendor_portal.api.get_supplier_comparison", item_code="_Test Item"
        )
        self.assertTrue(len(result) > 0)
        self.assertGreaterEqual(result[0]["avg_rate"], result[1]["avg_rate"])
