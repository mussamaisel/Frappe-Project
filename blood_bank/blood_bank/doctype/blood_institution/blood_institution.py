# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class BloodInstitution(NestedSet):
    def after_insert(self):
        if self.institution_type == "Partner Hospital":
            self.create_nbts_partnership()

    def create_nbts_partnership(self):
        nbts_root = frappe.db.get_single_value("Blood Bank Settings", "nbts_root_institution")

        if not nbts_root:
            frappe.msgprint(
                "NBTS Root Institution is not set in Blood Bank Settings. "
                "Institution Partnership was not created automatically.",
                indicator="orange",
                alert=True,
            )
            return

        if frappe.db.exists(
            "Institution Partnership",
            {"requesting_institution": self.name, "supplying_institution": nbts_root},
        ):
            return

        frappe.get_doc(
            {
                "doctype": "Institution Partnership",
                "requesting_institution": self.name,
                "supplying_institution": nbts_root,
                "status": "Approved",
            }
        ).insert(ignore_permissions=True)