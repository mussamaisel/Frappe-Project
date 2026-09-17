# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days


class BloodCollection(Document):
    def on_submit(self):
        self.create_blood_unit()
        self.update_donor_eligibility()
        self.mark_appointment_donated()

    def create_blood_unit(self):
        settings = frappe.get_single("Blood Bank Settings")
        collection_date = getdate(self.collection_datetime)
        component_type = "Whole Blood"

        expiry_days_map = {
            "Whole Blood": settings.expiry_days_whole_blood,
            "Packed Red Cells": settings.expiry_days_packed_red_cells,
            "Plasma": settings.expiry_days_plasma,
            "Platelets": settings.expiry_days_platelets,
            "Cryoprecipitate": settings.expiry_days_cryoprecipitate,
        }

        blood_unit = frappe.new_doc("Blood Unit")
        blood_unit.blood_collection = self.name
        blood_unit.blood_group = self.blood_group
        blood_unit.component_type = component_type
        blood_unit.collection_date = collection_date
        blood_unit.expiry_date = add_days(collection_date, expiry_days_map[component_type])
        blood_unit.custodian_institution = self.blood_institution
        blood_unit.status = "In Testing"
        blood_unit.insert()

        frappe.msgprint(f"Blood Unit {blood_unit.name} was created automatically.")

    def update_donor_eligibility(self):
        donor = frappe.get_doc("Donor", self.donor)
        settings = frappe.get_single("Blood Bank Settings")

        interval_days = (
            settings.donation_interval_female
            if donor.gender == "Female"
            else settings.donation_interval_male
        )

        donor.last_donation_date = getdate(self.collection_datetime)
        donor.next_eligible_date = add_days(donor.last_donation_date, interval_days)
        donor.total_donations = (donor.total_donations or 0) + 1
        donor.save(ignore_permissions=True)

    def mark_appointment_donated(self):
        if self.appointment:
            frappe.db.set_value("Appointment", self.appointment, "status", "Donated")