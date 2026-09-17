import frappe


def assign_donor_role(doc, method=None):
    if doc.user_type == "Website User":
        if "Donator" not in [role.role for role in doc.roles]:
            doc.append("roles", {"role": "Donator"})
            doc.save(ignore_permissions=True)
