import frappe


def after_insert_vendor_onboarding(doc, method):
    if not doc.email:
        return

    message = f"""
    <h3>Welcome to Vendor Portal 🎉</h3>
    <p>Dear {doc.supplier_name or "Vendor"},</p>

    <p>Your onboarding request has been received and is under review.</p>

    <p>We will notify you once the review is complete.</p>

    <br>
    <p>Regards,<br>Vendor Team</p>
    """

    frappe.sendmail(
        recipients=[doc.email],
        subject="Vendor Onboarding Received",
        message=message,
    )