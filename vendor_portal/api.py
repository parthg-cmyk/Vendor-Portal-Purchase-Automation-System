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


@frappe.whitelist()
def get_vendor_dashboard(supplier):
    if not supplier:
        frappe.throw("Supplier is required")

    data = {}

    # -----------------------------
    # 📦 Purchase Orders
    # -----------------------------
    po_data = frappe.db.sql(
        """
        SELECT 
            COUNT(*) as total_pos,
            SUM(grand_total) as total_value
        FROM `tabPurchase Order`
        WHERE supplier = %s AND docstatus = 1
    """,
        (supplier,),
        as_dict=True,
    )[0]

    data["total_pos"] = po_data.total_pos or 0
    data["total_po_value"] = po_data.total_value or 0

    # -----------------------------
    # 📥 Purchase Receipts
    # -----------------------------
    pr_data = frappe.db.sql(
        """
        SELECT 
            COUNT(*) as total_receipts,
            SUM(CASE WHEN status != 'Completed' THEN 1 ELSE 0 END) as pending_receipts
        FROM `tabPurchase Receipt`
        WHERE supplier = %s AND docstatus = 1
    """,
        (supplier,),
        as_dict=True,
    )[0]

    data["total_receipts"] = pr_data.total_receipts or 0
    data["pending_receipts"] = pr_data.pending_receipts or 0

    # -----------------------------
    # 💰 Purchase Invoices
    # -----------------------------
    pi_data = frappe.db.sql(
        """
        SELECT 
            SUM(grand_total) as total_invoiced,
            SUM(outstanding_amount) as outstanding_amount
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND docstatus = 1
    """,
        (supplier,),
        as_dict=True,
    )[0]

    data["total_invoiced"] = pi_data.total_invoiced or 0
    data["outstanding_amount"] = pi_data.outstanding_amount or 0

    # -----------------------------
    # ⭐ Ratings Summary
    # -----------------------------
    rating_data = frappe.db.sql(
        """
        SELECT 
            AVG(score) as avg_rating
        FROM `tabVendor Rating Log`
        WHERE supplier = %s
    """,
        (supplier,),
        as_dict=True,
    )[0]

    data["avg_rating"] = round(rating_data.avg_rating or 0, 2)

    # -----------------------------
    # ⭐ Rating Breakdown
    # -----------------------------
    breakdown = frappe.db.sql(
        """
        SELECT 
            rating_type,
            AVG(score) as avg_score,
            COUNT(*) as count
        FROM `tabVendor Rating Log`
        WHERE supplier = %s
        GROUP BY rating_type
    """,
        (supplier,),
        as_dict=True,
    )

    data["rating_breakdown"] = breakdown or []

    # -----------------------------
    # 🕒 Recent Ratings (last 10)
    # -----------------------------
    recent = frappe.db.sql(
        """
        SELECT 
            creation as date,
            rating_type,
            score,
            remarks
        FROM `tabVendor Rating Log`
        WHERE supplier = %s
        ORDER BY creation DESC
        LIMIT 10
    """,
        (supplier,),
        as_dict=True,
    )

    data["recent_ratings"] = recent or []

    return data


@frappe.whitelist()
def submit_vendor_rating(
    supplier,
    rating_type,
    score,
    remarks=None,
    purchase_order=None,
    purchase_receipt=None,
):
    # -----------------------------
    # 🔒 Validations
    # -----------------------------
    if not frappe.db.exists("Supplier", supplier):
        frappe.throw("Invalid Supplier")

    try:
        score = float(score)
    except:
        frappe.throw("Score must be a number")

    if score < 1 or score > 5:
        frappe.throw("Score must be between 1 and 5")

    # -----------------------------
    # ⚙️ Get Settings
    # -----------------------------
    settings = frappe.get_single("Vendor Portal Settings")

    weights = {
        "Delivery": settings.rating_weight_delivery or 1,
        "Pricing": settings.rating_weight_pricing or 1,
        "Communication": settings.rating_weight_communication or 1,
        # ⚠️ IMPORTANT: Quality not in settings → default 1
        "Quality": 1,
    }

    # -----------------------------
    # 🚫 Prevent duplicate rating (optional but recommended)
    # -----------------------------
    if purchase_order:
        exists = frappe.db.exists(
            "Vendor Rating Log",
            {
                "supplier": supplier,
                "purchase_order": purchase_order,
                "rating_type": rating_type,
            },
        )
        if exists:
            frappe.throw(
                f"Rating already exists for PO {purchase_order} ({rating_type})"
            )

    if purchase_receipt:
        exists = frappe.db.exists(
            "Vendor Rating Log",
            {
                "supplier": supplier,
                "purchase_receipt": purchase_receipt,
                "rating_type": rating_type,
            },
        )
        if exists:
            frappe.throw(
                f"Rating already exists for PR {purchase_receipt} ({rating_type})"
            )

    # -----------------------------
    # 📝 Create Rating Log
    # -----------------------------
    doc = frappe.get_doc(
        {
            "doctype": "Vendor Rating Log",
            "supplier": supplier,
            "purchase_order": purchase_order,
            "purchase_receipt": purchase_receipt,
            "rating_type": rating_type,
            "score": score,
            "remarks": remarks,
        }
    )

    doc.insert(ignore_permissions=True)

    # -----------------------------
    # 📊 Recalculate Weighted Rating
    # -----------------------------
    logs = frappe.db.sql(
        """
        SELECT rating_type, score
        FROM `tabVendor Rating Log`
        WHERE supplier = %s
    """,
        (supplier,),
        as_dict=True,
    )

    total_weighted_score = 0
    total_weight = 0

    for row in logs:
        weight = weights.get(row.rating_type, 1)
        total_weighted_score += row.score * weight
        total_weight += weight

    avg_rating = round(total_weighted_score / total_weight, 2) if total_weight else 0

    # -----------------------------
    # 🔄 Update Supplier
    # -----------------------------
    frappe.db.set_value(
        "Supplier",
        supplier,
        {"custom_vendor_rating": avg_rating, "custom_total_rating_count": len(logs)},
    )

    return {"status": "success", "avg_rating": avg_rating, "total_ratings": len(logs)}


@frappe.whitelist()
def get_supplier_comparison(item_code, qty=1):

    if not item_code:
        frappe.throw("Item Code is required")

    # -----------------------------
    # 📦 Supplier + Pricing Data
    # -----------------------------
    supplier_data = frappe.db.sql(
        """
        SELECT 
            po.supplier,
            poi.rate,
            poi.qty,
            po.transaction_date
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po
            ON poi.parent = po.name
        WHERE poi.item_code = %s
          AND po.docstatus = 1
        ORDER BY po.transaction_date DESC
    """,
        (item_code,),
        as_dict=True,
    )

    if not supplier_data:
        return []

    supplier_map = {}

    # -----------------------------
    # 📊 Aggregate Data
    # -----------------------------
    for row in supplier_data:
        supplier = row.supplier

        if supplier not in supplier_map:
            supplier_map[supplier] = {
                "supplier_name": supplier,
                "last_rate": row.rate,
                "total_rate": 0,
                "count": 0,
                "total_supplied_qty": 0,
            }

        supplier_map[supplier]["total_rate"] += row.rate
        supplier_map[supplier]["count"] += 1
        supplier_map[supplier]["total_supplied_qty"] += row.qty

    # -----------------------------
    # ⭐ Fetch Ratings
    # -----------------------------
    ratings = frappe.db.sql(
        """
        SELECT 
            supplier,
            AVG(score) as avg_rating,
            AVG(CASE WHEN rating_type = 'Delivery' THEN score END) as delivery_score
        FROM `tabVendor Rating Log`
        GROUP BY supplier
    """,
        as_dict=True,
    )

    rating_map = {r.supplier: r for r in ratings}

    # -----------------------------
    # 🔄 Final Format
    # -----------------------------
    result = []

    for supplier, data in supplier_map.items():

        avg_rate = data["total_rate"] / data["count"] if data["count"] else 0

        rating = rating_map.get(supplier, {})

        result.append(
            {
                "supplier_name": supplier,
                "last_rate": data["last_rate"],
                "avg_rate": round(avg_rate, 2),
                "vendor_rating": round(rating.get("avg_rating", 0) or 0, 2),
                "delivery_score": round(rating.get("delivery_score", 0) or 0, 2),
                "total_supplied_qty": data["total_supplied_qty"],
            }
        )

    # -----------------------------
    # 🔽 Sort (Best First)
    # -----------------------------
    result.sort(
        key=lambda x: (
            -x["vendor_rating"],  # higher rating first
            x["avg_rate"],  # lower price better
        )
    )

    return result


@frappe.whitelist(allow_guest=True)
def get_onboarding_status_summary():

    data = {}

    # -----------------------------
    # 📊 Status Counts
    # -----------------------------
    status_counts = frappe.db.sql(
        """
        SELECT 
            onboarding_status,
            COUNT(*) as count
        FROM `tabVendor Onboarding`
        GROUP BY onboarding_status
    """,
        as_dict=True,
    )

    # Default values
    data["total_pending"] = 0
    data["total_approved"] = 0
    data["total_rejected"] = 0

    # Map counts
    for row in status_counts:
        if row.onboarding_status == "Under Review":
            data["total_pending"] = row.count
        elif row.onboarding_status == "Approved":
            data["total_approved"] = row.count
        elif row.onboarding_status == "Rejected":
            data["total_rejected"] = row.count

    # -----------------------------
    # 🕒 Recent Submissions (last 10)
    # -----------------------------
    recent = frappe.db.sql(
        """
        SELECT 
            name,
            supplier_name,
            vendor_category,
            onboarding_status,
            creation
        FROM `tabVendor Onboarding`
        ORDER BY creation DESC
        LIMIT 10
    """,
        as_dict=True,
    )

    data["recent_submissions"] = recent or []

    return data
    