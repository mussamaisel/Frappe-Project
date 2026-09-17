# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CrossMatchTest(Document):
    def on_submit(self):
        if self.result == "Incompatible":
            frappe.msgprint(
                f"Blood Unit {self.blood_unit} is Incompatible with this patient sample. "
                "It must NOT be issued against this Blood Request.",
                indicator="red",
                alert=True,
            )