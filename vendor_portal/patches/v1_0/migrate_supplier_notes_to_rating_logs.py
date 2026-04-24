import frappe
from frappe.utils import nowdate


def execute():
    """
    Migrate Supplier comments into Vendor Rating Log
    using keyword-based sentiment detection.
    """

    # ✅ Keyword → (rating_type, score)
    KEYWORD_MAP = {
        "good": ("Quality", 4),
        "excellent": ("Quality", 5),
        "bad": ("Quality", 2),
        "poor": ("Quality", 1),

        "late": ("Delivery", 2),
        "late delivery": ("Delivery", 1),
        "on time": ("Delivery", 5),

        "expensive": ("Pricing", 2),
        "cheap": ("Pricing", 4),
        "costly": ("Pricing", 2),

        "communication issue": ("Communication", 2),
        "responsive": ("Communication", 5),
        "unresponsive": ("Communication", 1),
    }

    created = 0
    skipped = 0

    # ✅ Fetch comments linked to Supplier
    comments = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "Supplier",
            "comment_type": "Comment"
        },
        fields=["name", "reference_name", "content"]
    )

    for c in comments:
        content = (c.content or "").lower()
        supplier = c.reference_name

        if not content:
            continue

        matched = False

        for keyword, (rating_type, score) in KEYWORD_MAP.items():
            if keyword in content:

                # ✅ Prevent duplicate migration
                exists = frappe.db.exists(
                    "Vendor Rating Log",
                    {
                        "supplier": supplier,
                        "remarks": ["like", f"%{keyword}%"]
                    }
                )

                if exists:
                    skipped += 1
                    matched = True
                    break

                # ✅ Create rating log
                doc = frappe.get_doc({
                    "doctype": "Vendor Rating Log",
                    "supplier": supplier,
                    "rating_type": rating_type,
                    "score": score,
                    "remarks": f"Auto-migrated from comment: '{keyword}'",
                    "rating_date": nowdate()
                })

                doc.insert(ignore_permissions=True)
                created += 1
                matched = True
                break

        if not matched:
            skipped += 1

    frappe.db.commit()

    frappe.logger().info(
        f"[Vendor Portal Patch] Created {created} rating logs, Skipped {skipped}"
    )