import frappe


def execute():
    """
    Recalculate vendor rating and total rating count
    for all suppliers using Vendor Rating Log
    and weighted formula from Vendor Portal Settings.
    """

    # ✅ Get weights from settings
    settings = frappe.get_single("Vendor Portal Settings")

    weight_delivery = settings.rating_weight_delivery or 0
    weight_pricing = settings.rating_weight_pricing or 0
    weight_communication = settings.rating_weight_communication or 0

    # Remaining weight goes to Quality
    weight_quality = 1 - (weight_delivery + weight_pricing + weight_communication)

    # Fetch all suppliers
    suppliers = frappe.get_all("Supplier", fields=["name"])

    updated = 0

    for supplier in suppliers:
        supplier_name = supplier.name

        # Aggregate ratings per type
        ratings = frappe.db.sql("""
            SELECT
                rating_type,
                AVG(score) as avg_score,
                COUNT(*) as count
            FROM `tabVendor Rating Log`
            WHERE supplier = %s
            GROUP BY rating_type
        """, (supplier_name,), as_dict=True)

        if not ratings:
            # No ratings → reset values
            frappe.db.set_value(
                "Supplier",
                supplier_name,
                {
                    "custom_vendor_rating": 0,
                    "custom_total_rating_count": 0
                },
                update_modified=False
            )
            continue

        # Initialize
        avg_delivery = avg_quality = avg_pricing = avg_communication = 0
        total_count = 0

        for r in ratings:
            total_count += r.count

            if r.rating_type == "Delivery":
                avg_delivery = r.avg_score or 0
            elif r.rating_type == "Quality":
                avg_quality = r.avg_score or 0
            elif r.rating_type == "Pricing":
                avg_pricing = r.avg_score or 0
            elif r.rating_type == "Communication":
                avg_communication = r.avg_score or 0

        # ✅ Weighted formula
        overall_rating = (
            (avg_delivery * weight_delivery) +
            (avg_pricing * weight_pricing) +
            (avg_communication * weight_communication) +
            (avg_quality * weight_quality)
        )

        # Optional rounding
        overall_rating = round(overall_rating, 2)

        # Update supplier
        frappe.db.set_value(
            "Supplier",
            supplier_name,
            {
                "custom_vendor_rating": overall_rating,
                "custom_total_rating_count": total_count
            },
            update_modified=False
        )

        updated += 1

    # Commit once
    frappe.db.commit()

    frappe.logger().info(
        f"[Vendor Portal Patch] Recalculated ratings for {updated} suppliers"
    )