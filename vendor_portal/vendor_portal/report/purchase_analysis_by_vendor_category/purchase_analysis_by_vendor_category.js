frappe.query_reports["Purchase Analysis by Vendor Category"] = {
    "filters": [
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
        }
    ]
};