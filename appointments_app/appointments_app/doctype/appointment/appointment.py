import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class Appointment(Document):
	def validate(self):
		# Validate and format the contact number
		if not self.contact_number:
			frappe.throw("Please enter a valid contact number")

		if len(self.contact_number) == 10:
			self.contact_number = f"+91{self.contact_number}"
		elif len(self.contact_number) == 13 and self.contact_number.startswith("+91"):
			pass
		else:
			frappe.throw("Please enter a valid contact number")
			
			

	def after_insert(self):
		self.create_individual_queue()
		self.send_confirmation_message()

	def create_individual_queue(self):
		# Ensure all required fields are set
		for field in ["clinic", "doctor", "shift", "date"]:
			if not getattr(self, field):
				frappe.throw(f"Missing value for {field}")

	
		filters = {
			"date": self.date,
			"shift": self.shift,
			"clinic": self.clinic,
			"doctor": self.doctor
		}

		frappe.logger().info(f"[Queue Count Filters]: {filters}")

		existing_count = frappe.db.count("Appointment Queue", filters)
		next_queue_number = existing_count + 1


		q = frappe.new_doc("Appointment Queue")

		q.date = self.date
		q.shift = self.shift
		q.clinic = self.clinic
		q.doctor = self.doctor
		q.queue_number = next_queue_number             
		q.patient_name = self.patient_name
		q.status = "Pending"
		q.reminder_date = self.reminder_date

		q.save(ignore_permissions=True)

		
		frappe.cache.set_value(f"{frappe.session.sid}:queue_number", next_queue_number)


	def send_confirmation_message(self):
			shift_title = frappe.db.get_value("Schedule Shift", self.shift, "title")

			queue_number = frappe.db.get_value(
				"Appointment Queue", 
				{"date": self.date, "shift": self.shift, "clinic": self.clinic, "doctor": self.doctor, "patient_name": self.patient_name, "reminder_date": self.reminder_date}, 
				"queue_number"
			)

			message = (
				f"Hi {self.patient_name}, your appointment for {self.clinic} "
				f"on {self.date} ({shift_title}) has been booked and your queue number is {queue_number}."
			)

			frappe.enqueue(
				"appointments_app.utils.send_message",
				body=message,
				from_=frappe.db.get_single_value("Appointments Twilio Settings", "from_phone_number"),
				to=self.contact_number,
			)

