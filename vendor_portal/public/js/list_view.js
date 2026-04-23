frappe.listview_settings['Purchase Order'] = {
     add_fields: ["status", "per_received", "schedule_date", "supplier"],

     get_indicator: function(doc){
        if(doc.status == "Completed"){
            return ["Completed","green","status","=","Completed"]
        }

        if (doc.schedule_date && doc.per_received < 100) {
            let today = frappe.datetime.get_today();

            if (doc.schedule_date < today) {
                return ["Overdue", "red"];
            }
        }

        if (doc.status === "To Receive" || doc.per_received < 100) {
            return ["To Receive", "orange"];
        }
     },

     get_menu_items: function (doc){
        return [
            {
                label : "Quick Rate Supplier",
                action : function (){
                    open_rating_dialog(doc)
                }
            }
        ]
     }
}

function open_rating_dialog(doc) {

    if (!doc.supplier) {
        frappe.msgprint("No supplier found for this Purchase Order");
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: "Quick Rate Supplier",
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
                reqd: 1,
                description: "1 to 5"
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
                    supplier: doc.supplier,
                    rating_type: values.rating_type,
                    score: values.score,
                    remarks: values.remarks,
                    purchase_order: doc.name
                },
                callback: function () {
                    frappe.msgprint("Rating submitted successfully");
                    dialog.hide();
                }
            });
        }
    });

    dialog.show();
}