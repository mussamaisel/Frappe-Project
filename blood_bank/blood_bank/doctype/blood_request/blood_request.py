# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BloodRequest(Document):
    def validate(self):
        self.check_institution_partnership()

    def check_institution_partnership(self):
        if self.requesting_institution == self.supplying_institution:
            frappe.throw("Requesting Institution and Supplying Institution cannot be the same.")

        if self.status == "Draft":
            return

        partnership_exists = frappe.db.exists(
            "Institution Partnership",
            {
                "requesting_institution": self.requesting_institution,
                "supplying_institution": self.supplying_institution,
                "status": "Approved",
            },
        )

        if not partnership_exists:
            frappe.throw(
                f"No approved partnership exists between {self.requesting_institution} "
                f"and {self.supplying_institution}. This request cannot proceed."
            )