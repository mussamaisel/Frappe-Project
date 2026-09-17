# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class TransfusionReactionReport(Document):
    def validate(self):
        if not self.report_datetime:
            self.report_datetime = now_datetime()

    def on_submit(self):
        self.notify_custodian_institution()

    def notify_custodian_institution(self):
        institution = frappe.db.get_value("Blood Unit", self.blood_unit, "custodian_institution")
        frappe.msgprint(
            f"A {self.severity} {self.reaction_type} reaction has been recorded for Blood Unit "
            f"{self.blood_unit} (institution: {institution}). Please review immediately.",
            indicator="red",
            alert=True,
        )