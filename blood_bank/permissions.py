import frappe


def get_user_institutions(user):
    """
    Returns None if the user has no restriction (full access).
    Returns a list of Blood Institution names the user is restricted to.
    Returns an empty list if the user has System User access but no institution assigned at all.
    """
    if user in ("Administrator",) or "System Manager" in frappe.get_roles(user):
        return None

    institutions = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Blood Institution"},
        pluck="for_value",
    )
    return institutions


def build_or_condition(table, fields, institutions):
    if institutions is None:
        return ""

    if not institutions:
        return "1=0"

    values = ", ".join(frappe.db.escape(name) for name in institutions)
    conditions = [f"`{table}`.`{field}` in ({values})" for field in fields]
    return "(" + " or ".join(conditions) + ")"


def blood_request_query_conditions(user):
    user = user or frappe.session.user
    institutions = get_user_institutions(user)
    return build_or_condition(
        "tabBlood Request", ["requesting_institution", "supplying_institution"], institutions
    )


def institution_partnership_query_conditions(user):
    user = user or frappe.session.user
    institutions = get_user_institutions(user)
    return build_or_condition(
        "tabInstitution Partnership", ["requesting_institution", "supplying_institution"], institutions
    )


def blood_issue_query_conditions(user):
    user = user or frappe.session.user
    institutions = get_user_institutions(user)

    if institutions is None:
        return ""

    if not institutions:
        return "1=0"

    values = ", ".join(frappe.db.escape(name) for name in institutions)
    return f"""(`tabBlood Issue`.`issued_to` in ({values})
        or `tabBlood Issue`.`blood_request` in (
            select `name` from `tabBlood Request` where `supplying_institution` in ({values})
        ))"""