app_name = "vendor_portal"
app_title = "Vendor Portal"
app_publisher = "Parth"
app_description = "This is an Vendor Portal."
app_email = "parth.g@sanskartechnolab.com"
app_license = "mit"


fixtures = [
    {"dt": "Custom Field", "filters": [["dt", "=", "Supplier"]]},
    {"dt": "Workflow", "filters": [["name", "=", "Vendor Onboarding Approval"]]},
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "doc_type",
                "in",
                [
                    "Supplier",
                    "Vendor Onboarding",
                    "Purchase Order",
                    "Vendor Rating Log",
                ],
            ],
        ],
    },
    {
        "doctype": "Print Format",
        "filters": [
            ["name", "in", ["Vendor Enhanced PO"]],
        ],
    }
]

override_doctype_class = {
    "Purchase Order": "vendor_portal.overrides.purchase_order.CustomPurchaseOrder"
}

doc_events = {
    "Purchase Receipt": {
        "validate": "vendor_portal.overrides.purchase_receipt.validate",
        "on_submit": "vendor_portal.overrides.purchase_receipt.on_submit",
    },
    "Vendor Onboarding": {
        "after_insert": "vendor_portal.overrides.vendor_onboarding.after_insert_vendor_onboarding",
    },
    "Supplier": {
        "on_update": "vendor_portal.overrides.supplier.on_update_supplier",
    },
}

app_include_js = [
    "/assets/vendor_portal/js/purchase_order.js",
    "/assets/vendor_portal/js/purchase_order_list.js",
    "/assets/vendor_portal/js/supplier.js",
    "/assets/vendor_portal/js/vendor_onboarding.js",
    "/assets/vendor_portal/js/list_view.js",
    "/assets/vendor_portal/js/purchase_invoice.js",
    "/assets/vendor_portal/js/item.js",
]

jinja = {"methods": ["vendor_portal.utils.jinja.rating_stars"]}

has_permission = {
    "Vendor Rating Log": "vendor_portal.permissions.vendor_rating_log_has_permission"
}

permission_query_conditions = {
    "Vendor Onboarding": "vendor_portal.permissions.vendor_onboarding_query_conditions"
}

has_permission.update(
    {"Vendor Onboarding": "vendor_portal.permissions.vendor_onboarding_has_permission"}
)

scheduler_events = {
    "daily": ["vendor_portal.tasks.auto_calculate_vendor_ratings"],
    "hourly": ["vendor_portal.tasks.auto_rate_deliveries"],
    "weekly": ["vendor_portal.tasks.vendor_performance_digest"],
    "cron": {"0 9 * * *": ["vendor_portal.tasks.auto_expire_stale_onboardings"]},
}
