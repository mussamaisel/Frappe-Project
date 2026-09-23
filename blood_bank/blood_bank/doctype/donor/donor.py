# Copyright (c) 2026, JACKSON ANDREW and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff


class Donor(Document):
    def before_insert(self):
        if frappe.session.user != "Guest":
            self.auto_link_website_user()

    def validate(self):
        if self.is_new():
            self.validate_age()
            self.validate_consent()
            self.prevent_duplicate_profile()

    def after_insert(self):
        if frappe.session.user == "Guest":
            self.create_donor_account()

    def on_update(self):
        self.sync_user_permission()

    def auto_link_website_user(self):
        if self.linked_user_account:
            return
        user_type = frappe.db.get_value("User", frappe.session.user, "user_type")
        if user_type == "Website User":
            self.linked_user_account = frappe.session.user

    def validate_age(self):
        settings = frappe.get_single("Blood Bank Settings")
        age = date_diff(getdate(), self.date_of_birth) // 365
        if age < settings.min_donor_age or age > settings.max_donor_age:
            frappe.throw(
                f"Donor age must be between {settings.min_donor_age} and {settings.max_donor_age} years to register."
            )

    def validate_consent(self):
        if not self.data_consent:
            frappe.throw("You must agree to the Donor Terms & Privacy Policy to continue.")

    def prevent_duplicate_profile(self):
        if frappe.session.user == "Guest":
            if self.email and frappe.db.exists("User", self.email):
                frappe.throw("An account with this email already exists. Please login instead.")
        else:
            if self.linked_user_account:
                existing = frappe.db.exists(
                    "Donor",
                    {"linked_user_account": self.linked_user_account, "name": ["!=", self.name]},
                )
                if existing:
                    frappe.throw("A Donor profile already exists for this account.")

    def create_donor_account(self):
        if not self.email:
            frappe.throw("Email is required to create your donor account.")

        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": self.email,
                "first_name": self.full_name,
                "user_type": "System User",
                "send_welcome_email": 1,
            }
        )
        user.append("roles", {"role": "Donator"})

        blocked_modules = [
            "Automation", "Contacts", "Core", "Custom", "Desk",
            "Email", "Geo", "Integrations", "Printing", "Social",
            "Website", "Workflow",
        ]
        for module in blocked_modules:
            user.append("block_modules", {"module": module})

        user.insert(ignore_permissions=True)

        self.db_set("linked_user_account", self.email)
        self.db_set("owner", self.email)
        self.sync_user_permission()

        frappe.local.login_manager.login_as(self.email)

    def sync_user_permission(self):
        if not self.linked_user_account:
            return
        already_linked = frappe.db.exists(
            "User Permission",
            {"user": self.linked_user_account, "allow": "Donor", "for_value": self.name},
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