import frappe


@frappe.whitelist()
def get_supplier_details(supplier):
    doc = frappe.get_doc("Supplier", supplier)

    return {
        "vendor_rating": doc.get("vendor_rating", 0),
        "vendor_category": doc.get("vendor_category", ""),
        "total_rating_count": doc.get("total_rating_count", 0),
        "is_blacklisted": doc.get("is_blacklisted", 0),
    }


import frappe


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
