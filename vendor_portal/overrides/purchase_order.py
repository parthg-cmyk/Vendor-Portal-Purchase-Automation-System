import frappe
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder
from frappe import _


class CustomPurchaseOrder(PurchaseOrder):

    def validate(self):
        super().validate()

        if not self.supplier:
            return

        supplier = frappe.get_doc("Supplier", self.supplier)

        # 🚫 Block if blacklisted
        if supplier.get("is_blacklisted"):
            reason = supplier.get("blacklist_reason") or "No reason specified"
            frappe.throw(
                _(
                    f"Cannot create Purchase Order for blacklisted supplier {supplier.name}. "
                    f"Reason: {reason}"
                )
            )

        # ⭐ Rating threshold validation
        rating = supplier.get("vendor_rating") or 0
        category = supplier.get("vendor_category")

        if category:
            category_doc = frappe.get_doc("Vendor Category", category)
            threshold = category_doc.get("minimum_rating_threshold") or 0

            if rating < threshold:
                frappe.throw(
                    _(
                        f"Supplier {supplier.name} rating ({rating}) is below the minimum "
                        f"threshold ({threshold}) for {category}."
                    )
                )

        # 📝 Logging
        frappe.logger().info(f"PO {self.name} validated for supplier {self.supplier}")

    def on_submit(self):
        super().on_submit()

        if not self.supplier:
            return

        # Get average PO value for supplier
        avg = (
            frappe.db.sql(
                """
                SELECT AVG(grand_total)
                FROM `tabPurchase Order`
                WHERE supplier = %s AND docstatus = 1 AND name != %s
            """,
                (self.supplier, self.name),
            )[0][0]
            or 0
        )

        current = self.grand_total or 0

        score = 4  # default

        if avg:
            lower = avg * 0.9
            upper = avg * 1.1

            if current < lower:
                score = 5
            elif current > upper:
                score = 3
            else:
                score = 4

        # Create Vendor Rating Log
        rating_log = frappe.get_doc(
            {
                "doctype": "Vendor Rating Log",
                "supplier": self.supplier,
                "purchase_order": self.name,
                "rating_type": "Pricing",
                "score": score,
            }
        )

        rating_log.insert(ignore_permissions=True)

    def on_cancel(self):
        super().on_cancel()

        logs = frappe.get_all(
            "Vendor Rating Log",
            filters={
                "purchase_order": self.name,
            },
            pluck="name",
        )

        for log in logs:
            frappe.delete_doc("Vendor Rating Log", log, force=True)
