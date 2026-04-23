import frappe
from frappe import _


def validate(doc, method):

    has_short_delivery = False

    for item in doc.items:
        if not item.purchase_order or not item.po_detail:
            continue

        # Get ordered qty from PO Item
        po_item = frappe.db.get_value(
            "Purchase Order Item", item.po_detail, ["qty"], as_dict=True
        )

        if not po_item:
            continue

        ordered_qty = po_item.qty or 0
        received_qty = item.qty or 0

        if ordered_qty and received_qty < 0.9 * ordered_qty:
            has_short_delivery = True

    if has_short_delivery:
        doc.flags.has_short_delivery = True

        # Add comment
        doc.add_comment(
            "Comment",
            _("Short delivery detected: Received less than 90% of ordered quantity."),
        )

def on_submit(doc, method):

    if not doc.supplier:
        return

    has_short = getattr(doc.flags, "has_short_delivery", False)

    # Default assumptions
    is_late = False

    # Check delay using linked PO
    expected_dates = []

    for item in doc.items:
        if item.purchase_order:
            expected_date = frappe.db.get_value(
                "Purchase Order", item.purchase_order, "schedule_date"
            )
            if expected_date:
                expected_dates.append(expected_date)

    # Take latest expected date (strictest case)
    if expected_dates:
        max_expected = max(expected_dates)

        if doc.posting_date and max_expected:
            delay_days = (doc.posting_date - max_expected).days
            if delay_days > 2:
                is_late = True

    # 🎯 Score logic
    if not is_late and not has_short:
        score = 5
    elif not is_late and has_short:
        score = 4
    elif is_late and not has_short:
        score = 3
    else:
        score = 2

    # Create Vendor Rating Log
    rating_log = frappe.get_doc(
        {
            "doctype": "Vendor Rating Log",
            "supplier": doc.supplier,
            "purchase_receipt": doc.name,
            "rating_type": "Delivery",
            "score": score,
        }
    )

    rating_log.insert(ignore_permissions=True)
