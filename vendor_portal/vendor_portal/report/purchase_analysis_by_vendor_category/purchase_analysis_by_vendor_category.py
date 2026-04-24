import frappe

def execute(filters=None):
    filters = frappe._dict(filters or {})

    # Safe defaults
    filters.setdefault("vendor_category", None)
    filters.setdefault("from_date", None)
    filters.setdefault("to_date", None)

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)

    return columns, data, None, chart


def get_columns():
    return [
        {"label": "Vendor Category", "fieldname": "vendor_category", "fieldtype": "Link", "options": "Vendor Category", "width": 180},
        {"label": "Total Suppliers", "fieldname": "total_suppliers", "fieldtype": "Int"},
        {"label": "Active Suppliers", "fieldname": "active_suppliers", "fieldtype": "Int"},
        {"label": "Total PO Value", "fieldname": "total_po_value", "fieldtype": "Currency"},
        {"label": "Avg PO Value", "fieldname": "avg_po_value", "fieldtype": "Currency"},
        {"label": "Total Items Purchased", "fieldname": "total_items", "fieldtype": "Float"},
        {"label": "Avg Vendor Rating", "fieldname": "avg_rating", "fieldtype": "Float"},
        {"label": "Lowest Rating Supplier", "fieldname": "lowest_supplier", "fieldtype": "Data"}
    ]


def get_data(filters):
    conditions = ""

    # WHERE conditions
    if filters.vendor_category:
        conditions += " AND s.custom_vendor_category = %(vendor_category)s"

    if filters.from_date and filters.to_date:
        conditions += " AND po.transaction_date BETWEEN %(from_date)s AND %(to_date)s"

    data = frappe.db.sql(f"""
        SELECT
            s.custom_vendor_category AS vendor_category,

            COUNT(DISTINCT s.name) AS total_suppliers,

            COUNT(DISTINCT CASE WHEN s.disabled = 0 THEN s.name END) AS active_suppliers,

            -- Safe aggregation (avoid duplication)
            SUM(DISTINCT po.grand_total) AS total_po_value,

            AVG(po.grand_total) AS avg_po_value,

            -- Items from child table
            SUM(pri.qty) AS total_items,

            AVG(vrl.score) AS avg_rating,

            -- Lowest rating supplier
            SUBSTRING_INDEX(
                GROUP_CONCAT(
                    DISTINCT s.name ORDER BY vrl.score ASC
                ),
                ',', 1
            ) AS lowest_supplier

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

        GROUP BY s.custom_vendor_category

        ORDER BY total_po_value DESC
    """, filters, as_dict=1)

    return data


def get_chart(data):
    return {
        "data": {
            "labels": [d["vendor_category"] or "Unknown" for d in data],
            "datasets": [
                {
                    "name": "PO Value",
                    "values": [d["total_po_value"] or 0 for d in data]
                }
            ]
        },
        "type": "pie"
    }