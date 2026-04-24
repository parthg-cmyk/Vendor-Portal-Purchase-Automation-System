import frappe
from frappe import _
from vendor_portal.api import create_delivery_rating_for_pr

def validate(doc, method):

    has_short_delivery = False

    for item in doc.items:
        if not item.purchase_order or not item.purchase_order_item:            
            continue

        # Get ordered qty from PO Item
        po_item = frappe.db.get_value(
            "Purchase Order Item", item.purchase_order_item, ["qty"], as_dict=True
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
    create_delivery_rating_for_pr(doc.name)