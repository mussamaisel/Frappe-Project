# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff


class Appointment(Document):
    def before_insert(self):
        self.auto_link_donor()

    def auto_link_donor(self):
        if "Donator" not in frappe.get_roles(frappe.session.user):
            return

        own_donor = frappe.db.get_value("Donor", {"linked_user_account": frappe.session.user}, "name")
        if not own_donor:
            frappe.throw("Please complete your Donor profile before booking an appointment.")

        self.donor = own_donor

    def validate(self):
        if self.is_new():
            self.check_donor_eligibility()

    def check_donor_eligibility(self):
        donor = frappe.get_doc("Donor", self.donor)
        settings = frappe.get_single("Blood Bank Settings")

        if donor.status == "Permanently Deferred":
            frappe.throw(f"{donor.full_name} is permanently deferred and cannot donate.")

        if donor.status == "Blacklisted":
            frappe.throw(f"{donor.full_name} is blacklisted and cannot book an appointment.")

        if donor.status == "Temporarily Deferred":
            if donor.deferral_until and getdate(self.scheduled_datetime) < getdate(donor.deferral_until):
                frappe.throw(f"{donor.full_name} is temporarily deferred until {donor.deferral_until}.")

        age = date_diff(getdate(self.scheduled_datetime), donor.date_of_birth) // 365
        if age < settings.min_donor_age or age > settings.max_donor_age:
            frappe.throw(
                f"Donor age ({age}) is outside the allowed range "
                f"({settings.min_donor_age}-{settings.max_donor_age} years)."
            )

        if donor.weight_kg and donor.weight_kg < settings.min_weight_kg:
            frappe.throw(
                f"Donor weight ({donor.weight_kg} kg) is below the minimum required ({settings.min_weight_kg} kg)."
            )

        if donor.next_eligible_date and getdate(self.scheduled_datetime) < getdate(donor.next_eligible_date):
            frappe.throw(f"{donor.full_name} is not eligible to donate again until {donor.next_eligible_date}.")