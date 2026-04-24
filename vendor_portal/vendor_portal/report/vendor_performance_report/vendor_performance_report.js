frappe.query_reports["Vendor Performance Report"] = {
    "filters": [
        {
            "fieldname": "supplier",
            "label": "Supplier",
            "fieldtype": "Link",
            "options": "Supplier"
        },
        {
            "fieldname": "vendor_category",
            "label": "Vendor Category",
            "fieldtype": "Link",
            "options": "Vendor Category"
        },
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date"
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date"
        },
        {
            "fieldname": "min_rating",
            "label": "Minimum Rating",
            "fieldtype": "Float"
        }
    ]
};