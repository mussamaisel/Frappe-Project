# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Donor(Document):
    def before_insert(self):
        self.auto_link_website_user()

    def validate(self):
        self.prevent_duplicate_profile()

    def on_update(self):
        self.sync_user_permission()

    def auto_link_website_user(self):
        if self.linked_user_account:
            return

        user_type = frappe.db.get_value("User", frappe.session.user, "user_type")
        if user_type == "Website User":
            self.linked_user_account = frappe.session.user

    def prevent_duplicate_profile(self):
        if not self.linked_user_account or not self.is_new():
            return

        existing = frappe.db.exists(
            "Donor",
            {"linked_user_account": self.linked_user_account, "name": ["!=", self.name]},
        )
        if existing:
            frappe.throw("A Donor profile already exists for this account.")

    def sync_user_permission(self):
        if not self.linked_user_account:
            return

        already_linked = frappe.db.exists(
            "User Permission",
            {
                "user": self.linked_user_account,
                "allow": "Donor",
                "for_value": self.name,
            },
        )

        if already_linked:
            return

        frappe.get_doc(
            {
                "doctype": "User Permission",
                "user": self.linked_user_account,
                "allow": "Donor",
                "for_value": self.name,
                "apply_to_all_doctypes": 1,
            }
        ).insert(ignore_permissions=True)