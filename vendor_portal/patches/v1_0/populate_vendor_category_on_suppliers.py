import frappe


def execute():
    """
    Populate custom_vendor_category on Supplier
    based on supplier_group mapping.
    """

    # ✅ Mapping: Supplier Group → Vendor Category
    group_to_category_map = {
        "Raw Material": "Raw Materials",
        "Services": "IT Services",
        "Local": "Local Vendors",
        "International": "International Vendors",
        "Contractor": "Service Providers"
    }

    # Fetch suppliers needing update
    suppliers = frappe.get_all(
        "Supplier",
        filters={
            "supplier_group": ["is", "set"],
            "custom_vendor_category": ["in", ["", None]]
        },
        fields=["name", "supplier_group"]
    )

    unmapped = []
    updated_count = 0

    for supplier in suppliers:
        supplier_name = supplier.name
        group = supplier.supplier_group

        if group in group_to_category_map:
            category = group_to_category_map[group]

            # ✅ Update supplier
            frappe.db.set_value(
                "Supplier",
                supplier_name,
                "custom_vendor_category",
                category,
                update_modified=False
            )
            updated_count += 1

        else:
            unmapped.append(supplier_name)

    # ✅ Commit once (important in patches)
    frappe.db.commit()

    # ✅ Logging
    if unmapped:
        frappe.logger().warning(
            f"[Vendor Portal Patch] Unmapped Suppliers ({len(unmapped)}): {unmapped}"
        )

    frappe.logger().info(
        f"[Vendor Portal Patch] Updated {updated_count} suppliers with vendor category"
    )