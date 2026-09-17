# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class InstitutionPartnership(Document):
    def validate(self):
        self.prevent_self_partnership()
        self.prevent_duplicate_partnership()
        self.set_default_date_requested()

    def prevent_self_partnership(self):
        if self.requesting_institution == self.supplying_institution:
            frappe.throw("An institution cannot form a partnership with itself.")

    def prevent_duplicate_partnership(self):
        existing = frappe.db.exists(
            "Institution Partnership",
            {
                "requesting_institution": self.requesting_institution,
                "supplying_institution": self.supplying_institution,
                "name": ["!=", self.name],
            },
        )
        if existing:
            frappe.throw(
                f"A partnership between these two institutions already exists ({existing})."
            )

    def set_default_date_requested(self):
        if not self.date_requested:
            self.date_requested = today()

    def on_update(self):
        if self.status == "Approved" and not self.date_approved:
            self.db_set("date_approved", today())