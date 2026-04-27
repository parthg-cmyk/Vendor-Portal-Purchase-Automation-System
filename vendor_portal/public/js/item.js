frappe.ui.form.on('Item', {
    refresh(frm) {
        frm.add_custom_button('Compare Vendors', () => {
            open_supplier_comparison_dialog();
        });
    }
});

function open_supplier_comparison_dialog() {
    let dialog = new frappe.ui.Dialog({
        title: 'Vendor Comparison Matrix',
        size: 'extra-large',
        fields: [
            {
                label: 'Item',
                fieldname: 'item_code',
                fieldtype: 'Link',
                options: 'Item',
                reqd: 1
            },
            {
                label: 'Quantity',
                fieldname: 'qty',
                fieldtype: 'Float',
                default: 1
            },
            {
                fieldtype: 'HTML',
                fieldname: 'comparison_html'
            }
        ],
        primary_action_label: 'Compare',
        primary_action(values) {
            load_supplier_comparison(values, dialog);
        }
    });

    dialog.show();
}

function load_supplier_comparison(values, dialog) {
    frappe.call({
        method: "vendor_portal.api.get_supplier_comparison",
        args: {
            item_code: values.item_code,
            qty: values.qty
        },
        freeze: true,
        freeze_message: "Comparing suppliers...",
        callback: function (r) {
            let data = r.message || [];

            if (!data.length) {
                dialog.fields_dict.comparison_html.$wrapper.html(
                    `<p class="text-muted">No supplier data found</p>`
                );
                return;
            }

            // Find best price for highlighting
            let min_price = Math.min(...data.map(d => d.avg_rate));

            let html = `
                <div style="overflow-x:auto;">
                <table class="table table-bordered table-hover">
                    <thead class="thead-light">
                        <tr>
                            <th>Supplier</th>
                            <th>Last Price</th>
                            <th>Avg Price</th>
                            <th>Rating ⭐</th>
                            <th>Delivery % 🚚</th>
                            <th>Total Qty</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.forEach(d => {
                let highlight = d.avg_rate === min_price ? 'background:#e8f5e9;' : '';

                html += `
                    <tr style="${highlight}">
                        <td><b>${d.supplier_name}</b></td>
                        <td>${(d.last_rate || 0).toFixed(2)}</td>
                        <td>${(d.avg_rate || 0).toFixed(2)}</td>
                        <td>${(d.vendor_rating || 0).toFixed(1)}</td>
                        <td>${(d.delivery_score || 0).toFixed(1)}%</td>
                        <td>${d.total_supplied_qty || 0}</td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;

            dialog.fields_dict.comparison_html.$wrapper.html(html);
        }
    });
}