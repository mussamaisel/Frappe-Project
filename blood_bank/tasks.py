import frappe
from frappe.utils import today


def expire_blood_units():
    expirable_statuses = ["In Testing", "Quarantine", "Available", "Reserved"]

    expired_units = frappe.get_all(
        "Blood Unit",
        filters={
            "status": ["in", expirable_statuses],
            "expiry_date": ["<", today()],
        },
        pluck="name",
    )

    for unit_name in expired_units:
        frappe.db.set_value("Blood Unit", unit_name, "status", "Expired")

    if expired_units:
        frappe.logger().info(f"Blood Bank: {len(expired_units)} Blood Unit(s) marked as Expired.")


def notify_institution_users(institution, message):
    users = frappe.get_all(
        "User Permission",
        filters={"allow": "Blood Institution", "for_value": institution},
        pluck="user",
    )

    for user in users:
        frappe.get_doc(
            {
                "doctype": "ToDo",
                "allocated_to": user,
                "description": message,
                "reference_type": "Blood Institution",
                "reference_name": institution,
            }
        ).insert(ignore_permissions=True)


def check_low_stock():
    settings = frappe.get_single("Blood Bank Settings")
    threshold = settings.low_stock_threshold_units

    stock_counts = frappe.db.sql(
        """
        select custodian_institution, blood_group, count(*) as unit_count
        from `tabBlood Unit`
        where status = 'Available'
        group by custodian_institution, blood_group
        """,
        as_dict=True,
    )

    existing = {(row.custodian_institution, row.blood_group): row.unit_count for row in stock_counts}
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    institutions = frappe.get_all("Blood Institution", pluck="name")

    for institution in institutions:
        for group in blood_groups:
            count = existing.get((institution, group), 0)
            if count < threshold:
                notify_institution_users(
                    institution,
                    f"Low stock alert: {group} has only {count} unit(s) available (threshold: {threshold}).",
                )


def donor_eligibility_reminders():
    donors = frappe.get_all(
        "Donor",
        filters={"next_eligible_date": today(), "status": "Active"},
        fields=["name", "full_name", "email"],
    )

    for donor in donors:
        if not donor.email:
            continue

        try:
            frappe.sendmail(
                recipients=[donor.email],
                subject="You are eligible to donate blood again!",
                message=(
                    f"Dear {donor.full_name}, you are now eligible to donate blood again. "
                    "Thank you for your continued support in saving lives."
                ),
            )
        except Exception:
            frappe.log_error(
                title="Donor Reminder Email Failed",
                message=frappe.get_traceback(),
            )
