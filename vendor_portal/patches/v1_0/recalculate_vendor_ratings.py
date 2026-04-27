import frappe
from vendor_portal.api import calculate_vendor_rating


def execute():
    """
    Recalculate vendor rating and total rating count
    using same logic as calculate_vendor_rating()
    """

    suppliers = frappe.get_all("Supplier", fields=["name"])

    updated = 0

    for supplier in suppliers:
        supplier_name = supplier.name

        # ✅ Use existing function
        avg_rating, total_count = calculate_vendor_rating(supplier_name)

        # Update supplier
        frappe.db.set_value(
            "Supplier",
            supplier_name,
            {
                "custom_vendor_rating": avg_rating,
                "custom_total_rating_count": total_count
            },
            update_modified=False
        )

        updated += 1

    frappe.db.commit()

    frappe.logger().info(
        f"[Vendor Portal Patch] Recalculated ratings for {updated} suppliers"
    )