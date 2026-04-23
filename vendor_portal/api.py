import frappe


@frappe.whitelist(allow_guest=True)
def get_supplier_details(supplier):
    doc = frappe.get_doc("Supplier", supplier)

    return {
        "vendor_rating": doc.get("custom_vendor_rating", 0),
        "vendor_category": doc.get("custom_vendor_category", ""),
        "total_rating_count": doc.get("custom_total_rating_count", 0),
        "is_blacklisted": doc.get("custom_is_blacklisted", 0),
    }


@frappe.whitelist()
def get_vendor_rating_logs(supplier):
    return frappe.get_all(
        "Vendor Rating Log",
        filters={"supplier": supplier},
        fields=["creation as date", "rating_type", "score", "remarks"],
        order_by="creation desc",
    )


@frappe.whitelist()
def create_vendor_rating(supplier, rating_type, score, remarks=None):
    # Validate supplier
    if not frappe.db.exists("Supplier", supplier):
        frappe.throw("Invalid Supplier")

    # Validate score
    score = int(score)
    if score < 1 or score > 5:
        frappe.throw("Score must be between 1 and 5")

    # Create log
    doc = frappe.get_doc(
        {
            "doctype": "Vendor Rating Log",
            "supplier": supplier,
            "rating_type": rating_type,
            "score": score,
            "remarks": remarks,
        }
    )
    doc.insert(ignore_permissions=True)

    return {"status": "success"}


@frappe.whitelist()
def get_supplier_dashboard_data(supplier):
    data = {}

    # Total POs
    data["total_pos"] = frappe.db.count("Purchase Order", {"supplier": supplier})

    # Total Value
    value = frappe.db.sql(
        """
        SELECT SUM(grand_total) as total
        FROM `tabPurchase Order`
        WHERE supplier = %s AND docstatus = 1
    """,
        (supplier,),
        as_dict=True,
    )

    data["total_value"] = value[0].total or 0

    # Ratings
    rating = frappe.db.sql(
        """
        SELECT AVG(score) as avg, COUNT(*) as count
        FROM `tabVendor Rating Log`
        WHERE supplier = %s
    """,
        (supplier,),
        as_dict=True,
    )[0]

    data["avg_rating"] = round(rating.avg or 0, 2)
    data["total_ratings"] = rating.count or 0

    return data


@frappe.whitelist()
def blacklist_supplier(supplier, reason):
    frappe.db.set_value(
        "Supplier",
        supplier,
        {"custom_is_blacklisted": 1, "custom_blacklist_reason": reason},
    )
    return {"status": "success"}


@frappe.whitelist()
def get_vendor_settings():
    # Replace with your settings doctype if exists
    return {"low_rating_threshold": 2}


@frappe.whitelist()
def approve_vendor_onboarding(docname):
    doc = frappe.get_doc("Vendor Onboarding", docname)
    doc.onboarding_status = "Approved"
    doc.save(ignore_permissions=True)
    return {"status": "approved"}


@frappe.whitelist()
def reject_vendor_onboarding(docname, reason):
    doc = frappe.get_doc("Vendor Onboarding", docname)
    doc.onboarding_status = "Rejected"
    doc.rejection_reason = reason
    doc.save(ignore_permissions=True)
    return {"status": "rejected"}


@frappe.whitelist()
def get_category_threshold(category):
    doc = frappe.get_doc("Vendor Category", category)

    return {"data": doc.minimum_rating_threshold}
