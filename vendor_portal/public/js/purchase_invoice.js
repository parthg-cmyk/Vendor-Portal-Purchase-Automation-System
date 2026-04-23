frappe.ui.form.on('Purchase Invoice', {
    refresh(frm) {

        if (!frm.doc.supplier) return;

        frappe.call({
            method: "vendor_portal.api.get_supplier_details",
            args: {
                supplier: frm.doc.supplier
            },
            callback: function (r) {
                if (r.message) {
                    let rating = r.message.vendor_rating || 0;

                    // Clear previous headline to avoid stacking
                    frm.dashboard.clear_headline();

                    if (rating < 3) {
                        frm.dashboard.set_headline_alert(
                            `Note: This supplier has a low vendor rating (${rating}/5). Consider reviewing vendor performance.`,
                            "orange"
                        );
                    }
                }
            }
        });
    }
});