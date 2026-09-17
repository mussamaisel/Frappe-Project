# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BloodIssue(Document):
    def validate(self):
        self.fetch_blood_unit_details()

    def on_submit(self):
        self.validate_blood_request_status()
        self.transfer_blood_units()
        self.update_blood_request_fulfillment()
        self.notify_donors()

    def notify_donors(self):
        institution_name = frappe.db.get_value("Blood Institution", self.issued_to, "institution_name")

        for row in self.blood_units:
            donor_info = frappe.db.sql(
                """
                select d.name, d.full_name, d.email
                from `tabBlood Unit` bu
                inner join `tabBlood Collection` bc on bc.name = bu.blood_collection
                inner join `tabDonor` d on d.name = bc.donor
                where bu.name = %s
                """,
                (row.blood_unit,),
                as_dict=True,
            )

            if not donor_info:
                continue

            donor = donor_info[0]
            if not donor.email:
                continue

            try:
                frappe.sendmail(
                    recipients=[donor.email],
                    subject="Your blood donation just saved a life!",
                    message=(
                        f"Dear {donor.full_name}, great news! Your blood donation "
                        f"(unit {row.blood_unit}) has just been issued to {institution_name} "
                        "and is on its way to help a patient in need. Thank you for your generosity."
                    ),
                )
            except Exception:
                frappe.log_error(
                    title="Donor Feedback Email Failed",
                    message=frappe.get_traceback(),
                )

    def fetch_blood_unit_details(self):
        for row in self.blood_units:
            unit = frappe.db.get_value(
                "Blood Unit", row.blood_unit, ["blood_group", "component_type"], as_dict=True
            )
            row.blood_group = unit.blood_group
            row.component_type = unit.component_type

    def validate_blood_request_status(self):
        request_status = frappe.db.get_value("Blood Request", self.blood_request, "status")
        if request_status not in ("Approved", "Partially Fulfilled"):
            frappe.throw(
                f"Cannot issue blood units against a Blood Request with status '{request_status}'. "
                "The request must be Approved first."
            )

    def transfer_blood_units(self):
        supplying_institution = frappe.db.get_value("Blood Request", self.blood_request, "supplying_institution")
        requires_cross_match = frappe.db.get_value("Blood Request", self.blood_request, "requires_cross_match")

        for row in self.blood_units:
            blood_unit = frappe.get_doc("Blood Unit", row.blood_unit)

            if blood_unit.status != "Available":
                frappe.throw(f"Blood Unit {blood_unit.name} is not Available (current status: {blood_unit.status}).")

            if blood_unit.custodian_institution != supplying_institution:
                frappe.throw(
                    f"Blood Unit {blood_unit.name} does not belong to the supplying institution of this request."
                )

            if requires_cross_match:
                compatible = frappe.db.exists(
                    "Cross Match Test",
                    {
                        "blood_request": self.blood_request,
                        "blood_unit": blood_unit.name,
                        "result": "Compatible",
                        "docstatus": 1,
                    },
                )
                if not compatible:
                    frappe.throw(
                        f"Blood Unit {blood_unit.name} requires a Compatible Cross Match Test "
                        "before it can be issued against this request."
                    )

            blood_unit.custodian_institution = self.issued_to
            blood_unit.status = "Issued"
            blood_unit.save(ignore_permissions=True)

    def update_blood_request_fulfillment(self):
        blood_request = frappe.get_doc("Blood Request", self.blood_request)
        units_issued_now = len(self.blood_units)

        blood_request.units_fulfilled = (blood_request.units_fulfilled or 0) + units_issued_now

        if blood_request.units_fulfilled >= blood_request.units_needed:
            blood_request.status = "Fulfilled"
        else:
            blood_request.status = "Partially Fulfilled"

        blood_request.save(ignore_permissions=True)