# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

REQUIRED_TEST_TYPES = ["HIV", "Hepatitis B", "Hepatitis C", "Syphilis", "Malaria"]


class BloodScreeningTest(Document):
    def on_submit(self):
        if self.result == "Reactive":
            self.discard_blood_unit()
        else:
            self.check_and_release_blood_unit()

    def discard_blood_unit(self):
        frappe.db.set_value("Blood Unit", self.blood_unit, "status", "Discarded")
        frappe.msgprint(
            f"Blood Unit {self.blood_unit} has been discarded due to a reactive {self.test_type} result."
        )

    def check_and_release_blood_unit(self):
        blood_unit = frappe.get_doc("Blood Unit", self.blood_unit)

        if blood_unit.status == "Discarded":
            return

        completed_tests = frappe.get_all(
            "Blood Screening Test",
            filters={"blood_unit": self.blood_unit, "docstatus": 1},
            fields=["test_type", "result"],
        )

        completed_types = {test.test_type for test in completed_tests}
        any_reactive = any(test.result == "Reactive" for test in completed_tests)

        if any_reactive:
            self.discard_blood_unit()
            return

        if completed_types.issuperset(REQUIRED_TEST_TYPES):
            frappe.db.set_value("Blood Unit", self.blood_unit, "status", "Available")
            frappe.msgprint(f"Blood Unit {self.blood_unit} has passed all screening tests and is now Available.")
