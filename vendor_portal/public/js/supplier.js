frappe.ui.form.on('Supplier', {
    refresh(frm) {
        load_supplier_dashboard(frm);

        add_blacklist_button(frm);

        add_onboarding_button(frm);

        show_low_rating_warning(frm);
    }
})

function load_supplier_dashboard(frm) {
    if (!frm.doc.name) return;

    frappe.call({
        method: "vendor_portal.api.get_supplier_dashboard_data",
        args :{
            supplier : frm.doc.name
        },
        callback : function (r){
            if (r.message){
                let data = r.message;

                frm.dashboard.clear_headline();

                frm.dashboard.set_headline(`
                    Total POs: ${data.total_pos || 0} |
                    Total Value: ₹ ${data.total_value || 0} |
                    Avg Rating: ${data.avg_rating || 0} ⭐ |
                    Total Ratings: ${data.total_ratings || 0}
                `);
            }
        }
    })
}

function add_blacklist_button(frm) {

    // Only for Purchase Manager
    if (!frappe.user.has_role("Purchase Manager")) return;

    if (frm.doc.is_blacklisted) return;

    frm.add_custom_button("Blacklist Supplier", () => {

        frappe.prompt(
            [
                {
                    label: "Reason",
                    fieldname: "reason",
                    fieldtype: "Small Text",
                    reqd: 1
                }
            ],
            function (values) {

                frappe.call({
                    method: "vendor_portal.api.blacklist_supplier",
                    args: {
                        supplier: frm.doc.name,
                        reason: values.reason
                    },
                    callback: function () {
                        frappe.msgprint("Supplier blacklisted successfully");
                        frm.reload_doc();
                    }
                });

            },
            "Blacklist Supplier",
            "Submit"
        );

    }, "Actions");
}

function add_onboarding_button(frm) {

    if (!frm.doc.custom_onboarding_reference) return;

    frm.add_custom_button("View Onboarding", () => {

        frappe.set_route(
            "Form",
            "Vendor Onboarding",
            frm.doc.custom_onboarding_reference
        );

    }, "View");
}

function show_low_rating_warning(frm) {

    frappe.call({
        method: "vendor_portal.api.get_vendor_settings",
        callback: function (r) {
            if (!r.message) return;

            let threshold = r.message.low_rating_threshold || 2;

            if (frm.doc.custom_vendor_rating < threshold) {

                frm.dashboard.set_headline_alert(
                    "Low Rating — Review Required",
                    "orange"
                );
            }
        }
    });
}