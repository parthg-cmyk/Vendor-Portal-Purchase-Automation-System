import frappe
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})

    # Safe defaults
    filters.setdefault("supplier", None)
    filters.setdefault("vendor_category", None)
    filters.setdefault("from_date", None)
    filters.setdefault("to_date", None)
    filters.setdefault("min_rating", None)

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)

    return columns, data, None, chart


def get_columns():
    return [
        {"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 180},
        {"label": "Vendor Category", "fieldname": "vendor_category", "fieldtype": "Link", "options": "Vendor Category", "width": 150},
        {"label": "Total POs", "fieldname": "total_pos", "fieldtype": "Int", "width": 100},
        {"label": "Total PO Value", "fieldname": "total_po_value", "fieldtype": "Currency", "width": 140},
        {"label": "Avg Delivery Score", "fieldname": "avg_delivery", "fieldtype": "Float", "width": 130},
        {"label": "Avg Quality Score", "fieldname": "avg_quality", "fieldtype": "Float", "width": 130},
        {"label": "Avg Pricing Score", "fieldname": "avg_pricing", "fieldtype": "Float", "width": 130},
        {"label": "Overall Rating", "fieldname": "overall_rating", "fieldtype": "Float", "width": 130},
        {"label": "Total Receipts", "fieldname": "total_receipts", "fieldtype": "Int", "width": 120},
        {"label": "On-Time %", "fieldname": "on_time_percent", "fieldtype": "Percent", "width": 110},
        {"label": "Short Delivery Count", "fieldname": "short_delivery", "fieldtype": "Int", "width": 150},
    ]


def get_data(filters):
    conditions = ""
    having_condition = ""

    # WHERE conditions
    if filters.supplier:
        conditions += " AND s.name = %(supplier)s"

    if filters.vendor_category:
        conditions += " AND s.custom_vendor_category = %(vendor_category)s"

    if filters.from_date and filters.to_date:
        conditions += " AND po.transaction_date BETWEEN %(from_date)s AND %(to_date)s"

    # Dynamic HAVING (Solution 3)
    if filters.min_rating is not None:
        having_condition = "HAVING AVG(vrl.score) >= %(min_rating)s"

    data = frappe.db.sql(f"""
        SELECT
            s.name AS supplier,
            s.custom_vendor_category AS vendor_category,

            COUNT(DISTINCT po.name) AS total_pos,

            -- Prevent duplication due to joins
            SUM(DISTINCT po.grand_total) AS total_po_value,

            AVG(CASE WHEN vrl.rating_type='Delivery' THEN vrl.score END) AS avg_delivery,
            AVG(CASE WHEN vrl.rating_type='Quality' THEN vrl.score END) AS avg_quality,
            AVG(CASE WHEN vrl.rating_type='Pricing' THEN vrl.score END) AS avg_pricing,

            AVG(vrl.score) AS overall_rating,

            COUNT(DISTINCT pr.name) AS total_receipts,

            IFNULL(
                SUM(CASE WHEN pr.status = 'Completed' THEN 1 ELSE 0 END) /
                NULLIF(COUNT(DISTINCT pr.name), 0) * 100,
            0) AS on_time_percent,

            SUM(
                CASE 
                    WHEN pri.received_qty < pri.qty THEN 1 
                    ELSE 0 
                END
            ) AS short_delivery

        FROM `tabSupplier` s

        LEFT JOIN `tabPurchase Order` po 
            ON po.supplier = s.name AND po.docstatus = 1

        LEFT JOIN `tabPurchase Receipt` pr 
            ON pr.supplier = s.name AND pr.docstatus = 1

        LEFT JOIN `tabPurchase Receipt Item` pri 
            ON pri.parent = pr.name

        LEFT JOIN `tabVendor Rating Log` vrl 
            ON vrl.supplier = s.name

        WHERE 1=1 {conditions}

        GROUP BY s.name

        {having_condition}

        ORDER BY overall_rating DESC
    """, filters, as_dict=1)

    return data


def get_chart_data(data):
    top = data[:10]

    return {
        "data": {
            "labels": [d["supplier"] for d in top],
            "datasets": [
                {
                    "name": "Overall Rating",
                    "values": [d["overall_rating"] or 0 for d in top]
                }
            ]
        },
        "type": "bar"
    }