frappe.ui.form.on('Purchase Order', {
    refresh(frm) {

        // Avoid duplicate buttons
        frm.clear_custom_buttons();

        // Fetch supplier data once
        if (frm.doc.supplier) {
            fetch_supplier_details(frm);
        }

        // Buttons
        add_view_rating_history_button(frm);

        if (frm.doc.docstatus === 1) {
            add_rate_supplier_button(frm);
        }
    },

    supplier(frm) {
        if (frm.doc.supplier) {
            fetch_supplier_details(frm);
        }
    }
});

function fetch_supplier_details(frm) {
    frappe.call({
        method: "vendor_portal.api.get_supplier_details",
        args: {
            supplier: frm.doc.supplier
        },
        callback: function (r) {
            if (r.message) {
                let data = r.message;

                // Clear previous headline
                frm.dashboard.clear_headline();

                if (data.is_blacklisted) {
                    frm.dashboard.set_headline_alert(
                        "WARNING: This supplier is blacklisted!",
                        "red"
                    );
                    frm.disable_save();
                } else {
                    frm.dashboard.set_headline(`
                        Rating: ${data.vendor_rating || 0} ⭐ | 
                        Category: ${data.vendor_category || "N/A"} | 
                        Total Ratings: ${data.total_rating_count || 0}
                    `);
                    frm.enable_save();
                }
            }
        }
    });
}

function add_view_rating_history_button(frm) {
    frm.add_custom_button("View Vendor Rating History", () => {

        if (!frm.doc.supplier) {
            frappe.msgprint("Please select a supplier first");
            return;
        }

        frappe.call({
            method: "vendor_portal.api.get_vendor_rating_logs",
            args: {
                supplier: frm.doc.supplier
            },
            callback: function (r) {
                if (r.message) {
                    let logs = r.message;

                    let dialog = new frappe.ui.Dialog({
                        title: "Vendor Rating History",
                        size: "large",
                        fields: [
                            {
                                fieldname: "ratings_table",
                                fieldtype: "HTML"
                            }
                        ]
                    });

                    let table_html = `
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Rating Type</th>
                                    <th>Score</th>
                                    <th>Remarks</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${logs.map(log => `
                                    <tr>
                                        <td>${log.date || ""}</td>
                                        <td>${log.rating_type}</td>
                                        <td>${log.score}</td>
                                        <td>${log.remarks || ""}</td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    `;

                    dialog.fields_dict.ratings_table.$wrapper.html(table_html);
                    dialog.show();
                }
            }
        });

    }, "Actions");
}

function add_rate_supplier_button(frm) {
    frm.add_custom_button("Rate This Supplier", () => {

        if (!frm.doc.supplier) {
            frappe.msgprint("Please select a supplier first");
            return;
        }

        let dialog = new frappe.ui.Dialog({
            title: "Rate Supplier",
            fields: [
                {
                    label: "Rating Type",
                    fieldname: "rating_type",
                    fieldtype: "Select",
                    options: ["Quality", "Delivery", "Service"],
                    reqd: 1
                },
                {
                    label: "Score",
                    fieldname: "score",
                    fieldtype: "Int",
                    reqd: 1
                },
                {
                    label: "Remarks",
                    fieldname: "remarks",
                    fieldtype: "Small Text"
                }
            ],
            primary_action_label: "Submit",
            primary_action(values) {

                if (values.score < 1 || values.score > 5) {
                    frappe.msgprint("Score must be between 1 and 5");
                    return;
                }

                frappe.call({
                    method: "vendor_portal.api.create_vendor_rating",
                    args: {
                        supplier: frm.doc.supplier,
                        rating_type: values.rating_type,
                        score: values.score,
                        remarks: values.remarks
                    },
                    callback: function () {
                        frappe.msgprint("Rating submitted successfully");
                        dialog.hide();

                        // Refresh rating after submit
                        fetch_supplier_details(frm);
                    }
                });
            }
        });

        dialog.show();
    });
}