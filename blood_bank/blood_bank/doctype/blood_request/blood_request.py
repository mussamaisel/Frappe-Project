# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BloodRequest(Document):
    def before_insert(self):
        self.auto_link_requesting_institution()

    def auto_link_requesting_institution(self):
        if self.requesting_institution:
            return

        own_institutions = frappe.get_all(
            "User Permission",
            filters={"user": frappe.session.user, "allow": "Blood Institution"},
            pluck="for_value",
        )
        if len(own_institutions) == 1:
            self.requesting_institution = own_institutions[0]

    def validate(self):
        if self.requesting_institution == self.supplying_institution:
            frappe.throw("Requesting Institution and Supplying Institution cannot be the same.")

        self.validate_supplying_institution()

    def validate_supplying_institution(self):
        requesting_type = frappe.db.get_value(
            "Blood Institution", self.requesting_institution, "institution_type"
        )

        if requesting_type == "Partner Hospital":
            assigned_branch = frappe.db.get_value(
                "Blood Institution", self.requesting_institution, "parent_blood_institution"
            )
            if not assigned_branch:
                frappe.throw(
                    f"{self.requesting_institution} is not assigned to any NBTS Branch (no parent set). "
                    "Please contact the Blood Bank Admin."
                )
            if self.supplying_institution != assigned_branch:
                frappe.throw(
                    f"{self.requesting_institution} can only request blood from its "
                    f"assigned branch: {assigned_branch}."
                )

        elif requesting_type == "NBTS Branch":
            supplying_type = frappe.db.get_value(
                "Blood Institution", self.supplying_institution, "institution_type"
            )
            if supplying_type != "NBTS Branch":
                frappe.throw("An NBTS Branch can only request blood from another NBTS Branch, not a hospital.")


@frappe.whitelist()
def get_my_institution():
    institutions = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Blood Institution"},
        pluck="for_value",
    )
    return institutions[0] if len(institutions) == 1 else None