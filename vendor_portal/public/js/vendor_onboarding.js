frappe.ui.form.on('Vendor Onboarding', {
    refresh(frm) {
        add_approve_reject_buttons(frm);

        update_document_progress(frm);
    },

    vendor_category(frm) {
        fetch_min_rating_threshold(frm);
    },

    validate(frm) {
        validate_gst(frm);
    }
})


function add_approve_reject_buttons(frm) {

    if (!frappe.user.has_role("Purchase Manager")) return;
    if (frm.doc.status !== "Under Review") return;

    frm.add_custom_button("Approve", () => {
        frappe.call({
            method: "vendor_portal.api.approve_vendor_onboarding",
            args: {
                docname: frm.doc.name
            },
            callback: function () {
                frappe.msgprint("Vendor Approved");
                frm.reload_doc();
            }
        });
    }, "Actions");

    frm.add_custom_button("Reject", () => {
        frappe.prompt(
            [
                {
                    label: "Rejection Reason",
                    fieldname: "reason",
                    fieldtype: "Small Text",
                    reqd: 1
                }
            ],
            function (values) {
                frappe.call({
                    method: "vendor_portal.api.reject_vendor_onboarding",
                    args: {
                        docname: frm.doc.name,
                        reason: values.reason
                    },
                    callback: function () {
                        frappe.msgprint("Vendor Rejected");
                        frm.reload_doc();
                    }
                });
            },
            "Reject Vendor",
            "Submit"
        );
    }, "Actions");
}

function fetch_min_rating_threshold(frm) {

    if (!frm.doc.vendor_category) return;

    frappe.call({
        method: "vendor_portal.api.get_category_threshold",
        args: {
            category: frm.doc.vendor_category
        },
        callback: function (r) {
            if (r.message) {
                frappe.msgprint(`Minimum Threshold For ${frm.doc.vendor_category} is ${r.message.data}`)
            }
        }
    });
}

function validate_gst(frm) {

    if (!frm.doc.gst_number) return;

    let gst_regex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[0-9A-Z]{1}$/;

    if (!gst_regex.test(frm.doc.gst_number)) {
        frappe.msgprint("Invalid GST Number format");
        frappe.validated = false;
    }
}

function update_document_progress(frm) {

    if (!frm.doc.documents) return;

    let total = frm.doc.documents.length;
    let verified = frm.doc.documents.filter(d => d.is_verified).length;

    frm.dashboard.set_headline(
        `${verified} of ${total} documents verified`
    );
}
