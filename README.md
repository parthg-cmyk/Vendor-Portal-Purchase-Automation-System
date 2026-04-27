# Vendor Portal

A production-grade Frappe application that extends ERPNext's Buying module with comprehensive vendor management, automated onboarding workflows, intelligent rating systems, and advanced purchase automation capabilities.

## 📋 Overview

**Vendor Portal** is a custom Frappe app built for ERPNext v16+ that demonstrates mastery of both the Frappe Framework and ERPNext's core business workflows. This app sits at the intersection of framework expertise and domain knowledge, implementing vendor onboarding, purchase request automation, vendor rating, and custom reporting—all without modifying ERPNext core code.

### Why This Project?

This application mirrors production ERPNext development requirements by:
- Overriding ERPNext controllers (Purchase Order, Purchase Receipt, Purchase Invoice)
- Extending standard DocTypes via custom fields and hooks
- Building approval workflows that integrate with ERPNext's docstatus lifecycle
- Implementing background jobs for automated scoring and notifications
- Creating whitelisted APIs for external vendor access
- Building Script Reports with cross-module SQL joins (Buying + Stock + Accounts)
- Managing fixtures for upgrade-safe deployment

## 🚀 Features

### Core Functionality

- **Vendor Onboarding Workflow**: Streamlined vendor registration with document verification and approval process
- **Automated Rating System**: Multi-dimensional vendor scoring based on delivery, quality, pricing, and communication
- **Purchase Order Enhancement**: Intelligent validation against vendor ratings and blacklist status
- **Delivery Performance Tracking**: Automatic quality assessment on purchase receipts
- **Vendor Categorization**: Classification system with category-specific rating thresholds
- **Background Automation**: Scheduled jobs for rating calculation, performance digests, and stale onboarding management
- **Comprehensive Reporting**: SQL-based reports with vendor performance analytics and purchase analysis
- **Role-Based Access Control**: Fine-grained permissions for vendor managers and purchase teams

### Custom DocTypes

1. **Vendor Category** (`vendor_category`)
   - Vendor classification with rating thresholds
   - Payment terms templates
   - Active/inactive status management

2. **Vendor Onboarding** (`vendor_onboarding`) - Submittable
   - Complete vendor registration with KYC documents
   - GST and PAN validation
   - Approval workflow (Draft → Under Review → Approved/Rejected)
   - Auto-supplier creation upon approval

3. **Vendor Document** (Child Table)
   - Document type management (GST Certificate, PAN Card, Bank Statement, etc.)
   - Verification tracking with remarks

4. **Vendor Rating Log** (`vendor_rating_log`)
   - Multi-dimensional rating capture (Delivery/Quality/Pricing/Communication)
   - Transaction-linked ratings (PO/PR references)
   - Historical rating audit trail

5. **Vendor Portal Settings** (Single DocType)
   - Global configuration for onboarding rules
   - Rating weight customization
   - Auto-rating preferences

### ERPNext Extensions

#### Custom Fields on Supplier
- `vendor_category` - Link to Vendor Category
- `vendor_rating` - Auto-calculated average rating (1-5 stars)
- `total_rating_count` - Total ratings received
- `onboarding_reference` - Link to onboarding record
- `is_blacklisted` - Blacklist flag
- `blacklist_reason` - Reason for blacklisting

## 🛠️ Technical Architecture

### ERPNext Override Strategies

This project demonstrates two primary approaches to extending ERPNext functionality:

#### 1. `override_doctype_class` (Purchase Order)

**Used For**: Deep controller customization requiring full method override capability

**Implementation**: 
```python
# hooks.py
override_doctype_class = {
    "Purchase Order": "vendor_portal.overrides.purchase_order.CustomPurchaseOrder"
}
```

**Advantages**:
- Complete control over controller methods
- Ability to add new methods to the controller
- Clean inheritance pattern with `super()` calls
- Single point of override definition

**Trade-offs**:
- Entire class replacement (must call `super()` for all overridden methods)
- More tightly coupled to ERPNext controller structure
- Requires careful version compatibility management

**Use Cases in This Project**:
- Blacklist validation on PO creation
- Rating threshold enforcement
- Automatic pricing rating on PO submission
- Rating cleanup on PO cancellation

#### 2. `doc_events` Hooks (Purchase Receipt)

**Used For**: Cross-cutting concerns and event-based extensions

**Implementation**:
```python
# hooks.py
doc_events = {
    "Purchase Receipt": {
        "on_submit": "vendor_portal.overrides.purchase_receipt.on_submit",
        "validate": "vendor_portal.overrides.purchase_receipt.validate"
    }
}
```

**Advantages**:
- Loosely coupled, event-driven architecture
- Multiple apps can hook the same events without conflicts
- Easier to maintain across ERPNext version upgrades
- Clear separation of concerns

**Trade-offs**:
- Limited to specific lifecycle events
- Cannot override core controller logic
- Multiple hook points scattered across files
- Less control over execution order if multiple apps hook same events

**Use Cases in This Project**:
- Short delivery detection
- Automatic delivery rating based on timeliness and quantity accuracy
- Comment addition for validation flags

### Recommendation

**Use `override_doctype_class` when**:
- You need to fundamentally change controller behavior
- Multiple related methods need coordinated changes
- You're building app-specific core logic

**Use `doc_events` when**:
- Adding supplementary functionality alongside ERPNext's core logic
- Building features that should coexist with other apps
- Implementing audit trails, notifications, or logging
- Creating loosely-coupled integrations

For this project, the hybrid approach provides the best balance: critical validations use `override_doctype_class` for enforcement, while supplementary features like auto-rating use `doc_events` for flexibility.

## 📦 Installation

### Prerequisites

- Frappe Framework v16+
- ERPNext v16+
- Python 3.12+
- MariaDB 10.6+
- Node.js v24+

### Setup Instructions

```bash
# Initialize bench
bench init vendor-bench --frappe-branch version-16
cd vendor-bench

# Create site
bench new-site vendor.localhost

# Get ERPNext
bench get-app erpnext --branch version-16

# Install ERPNext
bench --site vendor.localhost install-app erpnext

# Get Vendor Portal app
bench get-app https://github.com/your-username/vendor_portal

# Install Vendor Portal
bench --site vendor.localhost install-app vendor_portal

# Migrate and sync
bench --site vendor.localhost migrate
bench --site vendor.localhost clear-cache

# Start development server
bench start
```

### Post-Installation Setup

1. **Run ERPNext Setup Wizard**:
   - Company: Sanskar Technologies Pvt Ltd
   - Chart of Accounts: India
   - Currency: INR
   - Create at least 2 Warehouses

2. **Create Test Data**:
   - Create 5+ test Items
   - Create 4+ Suppliers
   - Run basic Purchase cycle (PO → PR → PI) to verify ERPNext functionality

3. **Create Test Users**:
```bash
   # Vendor Manager
   bench --site vendor.localhost add-user vendor_mgr@test.com
   # Assign: Vendor Manager, Purchase Manager roles
   
   # Purchase User
   bench --site vendor.localhost add-user purchase_user@test.com
   # Assign: Purchase Team, Purchase User roles
```

4. **Configure Vendor Portal Settings**:
   - Navigate to: Vendor Portal Settings
   - Set rating weights (default: Delivery 30%, Quality 30%, Pricing 20%, Communication 20%)
   - Configure auto-rating preferences
   - Set minimum documents required for onboarding

## 🎯 Usage Guide

### Vendor Onboarding Flow

1. **Create Vendor Onboarding**:
   - Fill vendor details (name, company, GST, PAN, contact)
   - Select vendor category
   - Upload required documents (GST Certificate, PAN Card, etc.)
   - Submit for review

2. **Approval Process**:
   - Purchase Manager reviews submission
   - Verifies documents
   - Approves or rejects with reason
   - Upon approval: ERPNext Supplier auto-created

3. **Supplier Activation**:
   - Linked supplier record created automatically
   - Vendor category assigned
   - Ready for purchase transactions

### Vendor Rating System

#### Automatic Ratings

- **Pricing Rating**: Auto-created on PO submission
  - Score 5: Below average PO value (better pricing)
  - Score 4: Within 10% of average
  - Score 3: Above average PO value

- **Delivery Rating**: Auto-created on PR submission
  - Score 5: On-time + full quantity
  - Score 4: On-time but short delivery
  - Score 3: Late (>2 days) but full quantity
  - Score 2: Late + short delivery

#### Manual Ratings

- Quality and Communication ratings can be added manually via:
  - "Rate This Supplier" button on Purchase Order form
  - Direct Vendor Rating Log creation

#### Rating Calculation

Overall vendor rating is a weighted average:

vendor_rating = (delivery_avg × 0.3) + (quality_avg × 0.3) +
(pricing_avg × 0.2) + (communication_avg × 0.2)

Weights are configurable in Vendor Portal Settings.

### Purchase Order Validations

1. **Blacklist Check**: Blocks PO creation for blacklisted suppliers
2. **Rating Threshold**: Enforces minimum rating based on vendor category
3. **Automatic Logging**: All PO validations logged for audit

### Background Jobs

| Job | Frequency | Purpose |
|-----|-----------|---------|
| Auto-Calculate Vendor Ratings | Daily | Recalculates weighted average ratings for all suppliers |
| Auto-Rate Deliveries | Hourly | Creates delivery ratings for recent PRs |
| Vendor Performance Digest | Weekly | Sends performance summary email to Vendor Managers |
| Auto-Expire Stale Onboardings | Daily (9 AM) | Sends reminders and auto-rejects stale onboarding requests |

## 🔌 API Documentation

All APIs are whitelisted and accessible via `/api/method/vendor_portal.api.{method_name}`

### 1. Get Vendor Dashboard

```python
@frappe.whitelist()
def get_vendor_dashboard(supplier)
```

**Parameters**:
- `supplier` (str): Supplier name

**Returns**:
```json
{
  "total_pos": 150,
  "total_po_value": 5000000.00,
  "total_receipts": 145,
  "pending_receipts": 5,
  "avg_rating": 4.2,
  "rating_breakdown": {
    "Delivery": 4.5,
    "Quality": 4.3,
    "Pricing": 4.0,
    "Communication": 4.1
  },
  "recent_ratings": [...],
  "total_invoiced": 4800000.00,
  "outstanding_amount": 200000.00
}
```

### 2. Submit Vendor Rating

```python
@frappe.whitelist()
def submit_vendor_rating(supplier, rating_type, score, remarks, 
                        purchase_order=None, purchase_receipt=None)
```

**Parameters**:
- `supplier` (str): Supplier name
- `rating_type` (str): One of: Delivery, Quality, Pricing, Communication
- `score` (float): Rating score (1-5)
- `remarks` (str): Optional comments
- `purchase_order` (str): Optional PO reference
- `purchase_receipt` (str): Optional PR reference

**Returns**: Created Vendor Rating Log name

### 3. Get Supplier Comparison

```python
@frappe.whitelist()
def get_supplier_comparison(item_code, qty=1)
```

**Parameters**:
- `item_code` (str): Item Code
- `qty` (float): Quantity for rate comparison (default: 1)

**Returns**:
```json
[
  {
    "supplier_name": "Vendor A",
    "last_rate": 100.00,
    "avg_rate": 98.50,
    "vendor_rating": 4.5,
    "delivery_score": 4.8,
    "total_supplied_qty": 5000
  },
  ...
]
```

### 4. Get Onboarding Status Summary

```python
@frappe.whitelist()
def get_onboarding_status_summary()
```

**Returns**:
```json
{
  "total_pending": 15,
  "total_approved": 145,
  "total_rejected": 8,
  "recent_submissions": [...]
}
```

## 📊 Reports

### 1. Vendor Performance Report

**Type**: Script Report

**Filters**:
- Vendor Category
- Supplier
- Date Range (from_date, to_date)
- Minimum Rating

**Columns**:
- Supplier Name
- Vendor Category
- Total POs
- Total PO Value
- Avg Delivery Score
- Avg Quality Score
- Avg Pricing Score
- Overall Rating
- Total Receipts
- On-Time Delivery %
- Short Delivery Count

**Chart**: Bar chart showing top 10 suppliers by overall rating

### 2. Purchase Analysis by Vendor Category

**Type**: Script Report

**Filters**:
- Date Range
- Vendor Category

**Columns**:
- Vendor Category
- Total Suppliers
- Active Suppliers
- Total PO Value
- Avg PO Value
- Total Items Purchased
- Avg Vendor Rating
- Lowest Rating Supplier

**Chart**: Pie chart showing PO value distribution by vendor category

## 🔐 Roles & Permissions

### Vendor Manager

**Capabilities**:
- Full CRUD access to Vendor Onboarding
- Submit/Cancel Vendor Onboarding
- Approve/Reject vendor applications
- Full access to Vendor Rating Logs (all users)
- Blacklist/Un-blacklist suppliers
- Edit all vendor-related custom fields on Supplier
- Full access to all Vendor Portal reports
- Receive automated performance digests

**Permission Rules**:
- `has_permission`: Can edit all Vendor Rating Logs
- `permission_query_conditions`: Can view all Vendor Onboarding records

### Purchase Team

**Capabilities**:
- Create and submit Vendor Onboarding (for review)
- Create Vendor Rating Logs (own ratings only)
- Read-only access to Vendor Category
- Read-only access to Vendor Portal Settings
- Standard ERPNext Purchase User permissions (PO/PR/PI)

**Permission Rules**:
- `has_permission`: Can only edit own Vendor Rating Logs (where `rated_by` = current user)
- `permission_query_conditions`: Can only view own Vendor Onboarding submissions

## 🧪 Testing

### Running Tests

```bash
# Run all tests
bench --site vendor.localhost run-tests --app vendor_portal

# Run specific test file
bench --site vendor.localhost run-tests --app vendor_portal --module vendor_portal.vendor_portal.doctype.vendor_onboarding.test_vendor_onboarding

# Run with coverage
bench --site vendor.localhost run-tests --app vendor_portal --coverage
```

### Test Coverage

The project includes 14+ comprehensive unit tests covering:

#### Validation Tests
- GST format validation
- PAN format validation
- Minimum documents requirement
- Duplicate GST number blocking
- Blacklisted supplier PO blocking
- Low rating supplier PO blocking

#### Workflow Tests
- Vendor onboarding approval creates Supplier
- Vendor onboarding rejection with reason
- Linked supplier creation with correct field mapping

#### Rating Tests
- PO submission creates pricing rating
- PO cancellation deletes linked ratings
- PR submission creates delivery rating with correct score
- Weighted average rating calculation
- Rating recalculation accuracy

#### Permission Tests
- Purchase users can only edit own ratings
- Vendor Managers can edit all ratings
- Query condition filtering by user

#### API Tests
- Supplier comparison API returns correct sorted results
- Vendor dashboard API data accuracy

## 🔄 Data Migration Patches

### Patch Execution

```bash
bench --site vendor.localhost migrate
```

### Available Patches

1. **populate_vendor_category_on_suppliers.py** (v1.0)
   - Maps existing Supplier Groups to Vendor Categories
   - Logs unmapped suppliers for manual review

2. **recalculate_vendor_ratings.py** (v1.0)
   - Recalculates all supplier ratings from Vendor Rating Logs
   - Uses weighted formula from settings
   - Updates vendor_rating and total_rating_count

3. **migrate_supplier_notes_to_rating_logs.py** (v1.0)
   - Intelligently parses Supplier comments for rating keywords
   - Creates estimated Vendor Rating Log entries
   - Demonstrates intelligent data migration

## 🎨 Custom Print Format

**Purchase Order Print Format** includes:
- Standard PO details (items, quantities, rates)
- Vendor Category badge
- Vendor Rating displayed as star symbols (★★★★☆)
- Low rating caution notice (if rating < 3.0)
- Vendor Portal branding watermark
- Custom Jinja filter for star rating conversion

**Usage**: Select "Vendor Portal PO Format" from Print dropdown on Purchase Order

## 📁 Project Structure

vendor_portal/
├── vendor_portal/
│   ├── api.py                          # Whitelisted API methods
│   ├── tasks.py                        # Background job implementations
│   ├── hooks.py                        # App configuration and hooks
│   ├── patches/
│   │   └── v1_0/
│   │       ├── populate_vendor_category_on_suppliers.py
│   │       ├── recalculate_vendor_ratings.py
│   │       └── migrate_supplier_notes_to_rating_logs.py
│   ├── overrides/
│   │   ├── purchase_order.py          # PO controller override
│   │   └── purchase_receipt.py         # PR doc_events hooks
│   ├── vendor_portal/
│   │   └── doctype/
│   │       ├── vendor_category/
│   │       ├── vendor_onboarding/
│   │       ├── vendor_document/
│   │       ├── vendor_rating_log/
│   │       └── vendor_portal_settings/
│   ├── fixtures/                       # Custom fields, workflows
│   └── tests/
│       ├── test_api.py
├── public/
│   ├── js/
│   │   ├── vendor_portal.js           # Global JS overrides
│   │   ├── purchase_order.js          # PO form scripts
│   │   ├── supplier.js                # Supplier form scripts
│   │   └── vendor_onboarding.js       # Onboarding form scripts
│   └── css/
│       └── vendor_portal.css          # Custom styling
├── patches.txt                         # Patch execution order
├── README.md
└── license.txt

## ⚙️ Configuration Files

### hooks.py Highlights

```python
# DocType Class Overrides
override_doctype_class = {
    "Purchase Order": "vendor_portal.overrides.purchase_order.CustomPurchaseOrder"
}

# Document Events
doc_events = {
    "Purchase Receipt": {
        "on_submit": "vendor_portal.overrides.purchase_receipt.on_submit",
        "validate": "vendor_portal.overrides.purchase_receipt.validate"
    }
}

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "vendor_portal.tasks.auto_calculate_vendor_ratings",
        "vendor_portal.tasks.auto_expire_stale_onboardings"
    ],
    "hourly": [
        "vendor_portal.tasks.auto_rate_deliveries"
    ],
    "weekly": [
        "vendor_portal.tasks.vendor_performance_digest"
    ],
    "cron": {
        "0 9 * * *": [
            "vendor_portal.tasks.auto_expire_stale_onboardings"
        ]
    }
}

# Fixtures
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["name", "in", [
            "Supplier-vendor_category",
            "Supplier-vendor_rating",
            "Supplier-total_rating_count",
            "Supplier-onboarding_reference",
            "Supplier-is_blacklisted",
            "Supplier-blacklist_reason"
        ]]]
    },
    {
        "dt": "Workflow",
        "filters": [["name", "=", "Vendor Onboarding Approval"]]
    }
]

# JS/CSS Includes
app_include_js = "vendor_portal.bundle.js"
app_include_css = "vendor_portal.bundle.css"

# Permissions
permission_query_conditions = {
    "Vendor Onboarding": "vendor_portal.permissions.vendor_onboarding_query",
}

has_permission = {
    "Vendor Rating Log": "vendor_portal.permissions.vendor_rating_log_permission",
}

# Jinja Customization
jinja = {
    "methods": [
        "vendor_portal.utils.jinja.star_rating"
    ]
}
```

## 🚨 Important Notes & Best Practices

### Development Guidelines

1. **Never Modify Core**: All customizations via custom app only
2. **Always Call super()**: When overriding ERPNext controller methods
3. **Use frappe.throw()**: For all user-facing errors
4. **Parameterized SQL**: Never use string concatenation in queries
5. **Translations**: Use `frappe._("message")` for all user-facing strings
6. **Documentation**: Add docstrings to all Python functions
7. **Error Handling**: Wrap API logic in try-except and log with `frappe.log_error()`
8. **Transactions**: Use `frappe.db.commit()` after bulk operations
9. **Background Jobs**: Use `frappe.enqueue()` for long-running operations
10. **Validation**: Server-side validation is mandatory; client-side is UX enhancement only

### Upgrade Safety

- Custom fields exported as fixtures automatically restore after upgrades
- `override_doctype_class` requires version compatibility verification
- `doc_events` hooks are generally more upgrade-resilient
- Test on fresh sites before production deployment

## 🐛 Known Limitations

1. **Concurrent Rating Updates**: Multiple simultaneous ratings may require additional locking mechanism for large-scale deployments
2. **Performance**: With 500+ suppliers and 10,000+ POs, consider:
   - Database indexing on custom fields
   - Caching for frequently accessed vendor dashboards
   - Batch processing for background jobs
3. **GL Entry Integration**: Current implementation doesn't modify accounting entries; future enhancement could add vendor performance impact on payment terms

## 🔮 Future Enhancements

- **Vendor Self-Service Portal**: Web pages for vendor onboarding without Desk access
- **Supplier Scorecard Integration**: Enhance ERPNext's built-in Supplier Scorecard
- **Dashboard Page**: Custom Desk page with interactive charts
- **Bulk Vendor Import**: CSV-based bulk onboarding with `frappe.enqueue()`
- **Vendor Comparison Matrix**: Interactive side-by-side supplier comparison tool
- **Mobile App**: React Native app for vendor rating on-the-go
- **AI-Powered Insights**: Predictive analytics for vendor performance trends

## 📄 License

MIT License - See LICENSE.txt

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Commit Conventions

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or modifications
- `chore:` Maintenance tasks

## 📞 Support

For questions, issues, or feature requests:

- **GitHub Issues**: [Create an issue](https://github.com/your-username/vendor_portal/issues)
- **Email**: support@sanskartechnologies.com
- **Documentation**: [Wiki](https://github.com/your-username/vendor_portal/wiki)

## 👥 Authors

**Sanskar Technologies Pvt Ltd** - Developer Training Program Month 3 Assessment

## 🙏 Acknowledgments

- Frappe Framework team for the excellent framework
- ERPNext community for comprehensive documentation
- All contributors to the open-source ERPNext ecosystem

---

**Note**: This project is part of the Sanskar Developer Training Program final evaluation and demonstrates production-grade Frappe + ERPNext development practices.