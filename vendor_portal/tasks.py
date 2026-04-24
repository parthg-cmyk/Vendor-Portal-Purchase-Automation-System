import frappe
from vendor_portal.api import calculate_vendor_rating
from frappe.utils import now_datetime, add_to_date
from vendor_portal.api import create_delivery_rating_for_pr
from frappe.utils import nowdate, add_days, getdate


def auto_calculate_vendor_ratings():
    settings = frappe.get_single("Vendor Portal Settings")

    suppliers = frappe.get_all(
        "Supplier",
        filters={
            "disabled": 0,
            "custom_vendor_category": ["is", "set"],
        },
        pluck="name",
    )

    for supplier in suppliers:
        try:
            avg_rating, count = calculate_vendor_rating(supplier)

            # Update Supplier
            frappe.db.set_value(
                "Supplier",
                supplier,
                {
                    "custom_vendor_rating": avg_rating,
                    "custom_total_rating_count": count,
                },
            )

            # 🚨 Low Rating Alert
            if (
                settings.low_rating_threshold
                and avg_rating < settings.low_rating_threshold
            ):
                recipients = frappe.get_all(
                    "Has Role", filters={"role": "Vendor Manager"}, pluck="parent"
                )

                frappe.sendmail(
                    recipients=recipients,
                    subject=f"Low Vendor Rating Alert: {supplier}",
                    message=f"""
                        Supplier <b>{supplier}</b> rating dropped below threshold.<br><br>
                        <b>Current Rating:</b> {avg_rating}<br>
                        <b>Total Ratings:</b> {count}
                    """,
                )

        except Exception:
            frappe.log_error(
                title=f"Vendor Rating Failed: {supplier}",
                message=frappe.get_traceback(),
            )


def auto_rate_deliveries():
    two_hours_ago = add_to_date(now_datetime(), hours=-2)

    # Get submitted Purchase Receipts in last 2 hours
    receipts = frappe.get_all(
        "Purchase Receipt",
        filters={
            "docstatus": 1,
            "posting_date": [">=", two_hours_ago.date()],
        },
        pluck="name",
    )

    for pr in receipts:
        try:
            create_delivery_rating_for_pr(pr)

        except Exception:
            frappe.log_error(
                title=f"Auto Delivery Rating Failed: {pr}",
                message=frappe.get_traceback(),
            )


def vendor_performance_digest():
    settings = frappe.get_single("Vendor Portal Settings")

    today = getdate(nowdate())
    week_start = add_days(today, -7)

    # -----------------------------
    # 📊 Top 5 Vendors
    # -----------------------------
    top_vendors = frappe.get_all(
        "Supplier",
        filters={"disabled": 0},
        fields=["name", "custom_vendor_rating", "custom_total_rating_count"],
        order_by="custom_vendor_rating desc",
        limit=5,
    )

    # -----------------------------
    # 📉 Bottom 5 Vendors
    # -----------------------------
    bottom_vendors = frappe.get_all(
        "Supplier",
        filters={"disabled": 0},
        fields=["name", "custom_vendor_rating", "custom_total_rating_count"],
        order_by="custom_vendor_rating asc",
        limit=5,
    )

    # -----------------------------
    # 📦 Total POs this week
    # -----------------------------
    total_pos = frappe.db.count(
        "Purchase Order",
        filters={"transaction_date": ["between", [week_start, today]]},
    )

    # -----------------------------
    # 🆕 New Vendors this week
    # -----------------------------
    new_vendors = frappe.get_all(
        "Supplier",
        filters={"creation": [">=", week_start]},
        fields=["name", "creation"],
    )

    # -----------------------------
    # 🚨 Low Rating Vendors
    # -----------------------------
    low_rating_vendors = []

    if settings.low_rating_threshold:
        low_rating_vendors = frappe.get_all(
            "Supplier",
            filters={
                "custom_vendor_rating": ["<", settings.low_rating_threshold],
                "disabled": 0,
            },
            fields=["name", "custom_vendor_rating"],
        )

    # -----------------------------
    # 📨 Build HTML Email
    # -----------------------------
    def build_table(data, headers):
        if not data:
            return "<p>No data available</p>"

        rows = ""
        for row in data:
            rows += (
                "<tr>"
                + "".join(f"<td>{row.get(h, '')}</td>" for h in headers)
                + "</tr>"
            )

        return f"""
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color:#f2f2f2;">
                {''.join(f"<th>{h.replace('_', ' ').title()}</th>" for h in headers)}
            </tr>
            {rows}
        </table>
        """

    message = f"""
    <h2>📊 Weekly Vendor Performance Digest</h2>

    <h3>🏆 Top 5 Vendors</h3>
    {build_table(top_vendors, ["name", "custom_vendor_rating", "custom_total_rating_count"])}

    <h3>📉 Bottom 5 Vendors</h3>
    {build_table(bottom_vendors, ["name", "custom_vendor_rating", "custom_total_rating_count"])}

    <h3>📦 Total Purchase Orders (This Week)</h3>
    <p><b>{total_pos}</b></p>

    <h3>🆕 New Vendors Onboarded</h3>
    {build_table(new_vendors, ["name", "creation"])}

    <h3>🚨 Vendors Below Threshold</h3>
    {build_table(low_rating_vendors, ["name", "custom_vendor_rating"])}

    <br>
    <p>Regards,<br>Your Vendor Portal System</p>
    """

    # -----------------------------
    # 📧 Send Email
    # -----------------------------
    recipients = frappe.get_all(
        "Has Role", filters={"role": "Vendor Manager"}, pluck="parent"
    )
    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject="Weekly Vendor Performance Digest",
            message=message,
        )


def auto_expire_stale_onboardings():
    settings = frappe.get_single("Vendor Portal Settings")

    now = now_datetime()
    seven_days_ago = add_to_date(now, days=-7)
    fourteen_days_ago = add_to_date(now, days=-14)
    recipients = frappe.get_all(
        "Has Role", filters={"role": "Vendor Manager"}, pluck="parent"
    )

    # -----------------------------
    # 🔔 7+ Days → Reminder
    # -----------------------------
    stale_for_reminder = frappe.get_all(
        "Vendor Onboarding",
        filters={
            "onboarding_status": "Under Review",
            "creation": ["<=", seven_days_ago],
        },
        fields=["name", "supplier_name", "creation"],
    )

    # -----------------------------
    # ❌ 14+ Days → Auto Reject
    # -----------------------------
    stale_for_reject = frappe.get_all(
        "Vendor Onboarding",
        filters={
            "onboarding_status": "Under Review",
            "creation": ["<=", fourteen_days_ago],
        },
        fields=["name", "supplier_name"],
    )

    # -----------------------------
    # 📧 Send Reminder Email
    # -----------------------------
    if stale_for_reminder and recipients:

        rows = ""
        for row in stale_for_reminder:
            rows += f"""
                <tr>
                    <td>{row.name}</td>
                    <td>{row.supplier_name or ''}</td>
                    <td>{row.creation}</td>
                </tr>
            """

        message = f"""
        <h3>⏳ Pending Vendor Onboardings (7+ Days)</h3>
        <p>The following vendor onboardings are pending review:</p>

        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width:100%;">
            <tr style="background-color:#f2f2f2;">
                <th>ID</th>
                <th>Supplier Name</th>
                <th>Created On</th>
            </tr>
            {rows}
        </table>

        <br>
        <p>Please review them as soon as possible.</p>
        """

        frappe.sendmail(
            recipients=recipients,
            subject="Reminder: Pending Vendor Onboardings",
            message=message,
        )

    # -----------------------------
    # ❌ Auto Reject (14+ Days)
    # -----------------------------
    for row in stale_for_reject:
        try:
            doc = frappe.get_doc("Vendor Onboarding", row.name)

            doc.onboarding_status = "Rejected"
            doc.rejection_reason = "Auto-rejected: Review period expired."

            doc.save(ignore_permissions=True)

        except Exception:
            frappe.log_error(
                title=f"Auto Reject Failed: {row.name}",
                message=frappe.get_traceback(),
            )
