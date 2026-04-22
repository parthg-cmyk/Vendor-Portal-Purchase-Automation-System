# Copyright (c) 2026, Parth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VendorRatingLog(Document):

	def validate(self):
		self.validate_score()
	
	def validate_score(self):
		min_score = 1.0
		max_score = 5.0
		if not min_score <= self.score <= max_score:
			frappe.throw(f"Score must between {min_score} and {max_score}")
