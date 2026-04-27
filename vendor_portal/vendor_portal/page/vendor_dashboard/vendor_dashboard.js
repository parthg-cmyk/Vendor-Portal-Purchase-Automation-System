frappe.pages['vendor-dashboard'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Vendor Dashboard',
		single_column: true
	});

	$(wrapper).append(`
        <div class="row">
			<div class="col-md-6"><div id="rating-chart"></div></div>
            <div class="col-md-6"><div id="pipeline-chart"></div></div>
        </div>
        <div class="row mt-4">
            <div class="col-md-6"><div id="po-chart"></div></div>
            <div class="col-md-6"><div id="delivery-chart"></div></div>
        </div>
    `);

	load_rating_chart();
	load_pipeline_chart();
	load_po_chart();
	load_delivery_chart();
};

function load_rating_chart() {
	frappe.call({
		method: "vendor_portal.api.get_rating_distribution",
		callback: function (r) {
			new frappe.Chart("#rating-chart", {
				title: "Vendor Rating Distribution",
				data: {
					labels: r.message.map(d => d.bucket),
					datasets: [{
						values: r.message.map(d => d.count)
					}]
				},
				type: 'bar',
				height: 250
			});
		}
	});
}

// Pipeline
function load_pipeline_chart() {
	frappe.call({
		method: "vendor_portal.api.get_onboarding_pipeline",
		callback: function (r) {
			new frappe.Chart("#pipeline-chart", {
				title: "Vendor Pipeline",
				data: {
					labels: r.message.map(d => d.status),
					datasets: [{ values: r.message.map(d => d.count) }]
				},
				type: 'pie'
			});
		}
	});
}


// PO Category
function load_po_chart() {
	frappe.call({
		method: "vendor_portal.api.get_po_by_category",
		callback: function (r) {
			new frappe.Chart("#po-chart", {
				title: "PO by Category",
				data: {
					labels: r.message.map(d => d.category),
					datasets: [{ values: r.message.map(d => d.total) }]
				},
				type: 'bar'
			});
		}
	});
}


// Delivery Trend
function load_delivery_chart() {
	frappe.call({
		method: "vendor_portal.api.get_delivery_trend",
		callback: function (r) {
			new frappe.Chart("#delivery-chart", {
				title: "Delivery Trend",
				data: {
					labels: r.message.map(d => d.period),
					datasets: [{ values: r.message.map(d => d.value) }]
				},
				type: 'line'
			});
		}
	});
}