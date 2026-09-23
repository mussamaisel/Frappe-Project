// Copyright (c) 2026, JACKSON ANDREW and contributors
// For license information, please see license.txt

frappe.ui.form.on("Appointment", {
	onload(frm) {
		if (frm.is_new() && frappe.user_roles.includes("Donator")) {
			frappe.db.get_value("Donor", { "linked_user_account": frappe.session.user }, "name")
				.then((r) => {
					if (r.message && r.message.name) {
						frm.set_value("donor", r.message.name);
						frm.set_df_property("donor", "read_only", 1);
					}
				});
		}
	},
});