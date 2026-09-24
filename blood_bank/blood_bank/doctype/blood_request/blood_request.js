// Copyright (c) 2026, JACKSON ANDREW and contributors
// For license information, please see license.txt

frappe.ui.form.on("Blood Request", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.requesting_institution) {
			frappe.call({
				method: "blood_bank.blood_bank.doctype.blood_request.blood_request.get_my_institution",
			}).then((r) => {
				if (r.message) {
					frm.set_value("requesting_institution", r.message);
				}
			});
		}
	},

	requesting_institution(frm) {
		frm.trigger("apply_institution_logic");
	},

	apply_institution_logic(frm) {
		if (!frm.doc.requesting_institution) {
			return;
		}

		frappe.db.get_value(
			"Blood Institution",
			frm.doc.requesting_institution,
			["institution_type", "parent_blood_institution"]
		).then((r) => {
			const data = r.message;
			if (!data) return;

			if (data.institution_type === "Partner Hospital") {
				if (data.parent_blood_institution) {
					frm.set_value("supplying_institution", data.parent_blood_institution);
				}
				frm.set_df_property("supplying_institution", "read_only", 1);
			} else if (data.institution_type === "NBTS Branch") {
				frm.set_df_property("supplying_institution", "read_only", 0);
				frm.set_query("supplying_institution", () => ({
					filters: {
						institution_type: "NBTS Branch",
						name: ["!=", frm.doc.requesting_institution],
					},
				}));
			}
		});
	},
});