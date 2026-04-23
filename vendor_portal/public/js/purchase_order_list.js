frappe.listview_settings['Purchase Order'] = {
    add_fields: ["supplier_name", "grand_total", "per_received", "status"],

    get_indicator: function (doc) {
        if (doc.status === "Completed") {
            return [__("Completed"), "green", "status,=,Completed"];
        } else if (doc.status === "To Receive") {
            return [__("To Receive"), "orange", "status,=,To Receive"];
        }
    }
};