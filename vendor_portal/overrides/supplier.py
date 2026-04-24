import frappe


def on_update_supplier(doc, method):
    # Detect change in blacklist status
    if not doc.has_value_changed("custom_is_blacklisted"):
        return

    if doc.custom_is_blacklisted:
        action = "BLACKLISTED ❌"
    else:
        action = "REMOVED FROM BLACKLIST ✅"

    # Get Vendor Managers
    recipients = frappe.get_all(
        "Has Role",
        filters={"role": "Vendor Manager"},
        pluck="parent",
    )

    recipients = [
        user for user in recipients
        if user not in ("Administrator", "Guest")
        and frappe.db.get_value("User", user, "enabled")
    ]

    if not recipients:
        return

    message = f"""
    <h3>Supplier Status Update</h3>

    <p>Supplier <b>{doc.name}</b> has been <b>{action}</b>.</p>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=f"Supplier {action}: {doc.name}",
        message=message,
    )