import frappe

def vendor_rating_log_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user

    # Vendor Manager → full access
    if "Vendor Manager" in frappe.get_roles(user):
        return True

    # Only allow access to own ratings
    if doc.rated_by == user:
        return True

    return False

def vendor_onboarding_query_conditions(user):
    if "Vendor Manager" in frappe.get_roles(user):
        return ""

    if "Purchase Team" in frappe.get_roles(user):
        return f"`tabVendor Onboarding`.owner = '{user}'"

    # fallback (no access)
    return "1=0"

def vendor_onboarding_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user

    if "Vendor Manager" in frappe.get_roles(user):
        return True

    if "Purchase Team" in frappe.get_roles(user):
        return doc.owner == user

    return False