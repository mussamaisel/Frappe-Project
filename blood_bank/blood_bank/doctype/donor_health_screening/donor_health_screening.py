# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DonorHealthScreening(Document):
    def on_submit(self):
        self.update_appointment_status()
        self.apply_deferral_if_needed()

    def update_appointment_status(self):
        if not self.appointment:
            return

        new_status = "Screened" if self.eligibility_result == "Eligible" else "Deferred"
        frappe.db.set_value("Appointment", self.appointment, "status", new_status)

    def apply_deferral_if_needed(self):
        if self.eligibility_result == "Eligible":
            return

        appointment = frappe.get_doc("Appointment", self.appointment)
        donor = frappe.get_doc("Donor", appointment.donor)

        donor.status = self.eligibility_result
        donor.deferral_reason = f"Deferred based on screening {self.name}."
        donor.save(ignore_permissions=True)

        frappe.msgprint(
            f"Donor {donor.full_name} has been marked as '{self.eligibility_result}'. "
            "Please set the 'Deferral Until' date manually if applicable."
        )