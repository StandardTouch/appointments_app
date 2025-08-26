import frappe
from datetime import datetime, timedelta
from appointments_app.utils import send_message

def send_appointment_queue_reminders():
    today = datetime.now().date()

    appointment_queues = frappe.get_all("Appointment Queue",
        filters={
            "reminder_date": today,
            "status": "Pending"  
        },
        fields=[
            "name", "patient_name", "clinic", "shift", "doctor",
            "queue_number", "date"
        ]
    )

    for queue in appointment_queues:
        shift_title = frappe.db.get_value("Schedule Shift", queue.shift, "title")

        contact_number = frappe.db.get_value("Appointment",
            {
                "date": queue.date,
                "shift": queue.shift,
                "clinic": queue.clinic,
                "doctor": queue.doctor,
                "patient_name": queue.patient_name
            },
            "contact_number"
        )

        if not contact_number:
            frappe.log_error(f"No contact number found for Appointment Queue: {queue.name}")
            continue

        message = (
            f"Reminder: Hi {queue.patient_name}, your appointment at {queue.clinic} "
            f"on {queue.date} ({shift_title}) is tomorrow. Your queue number is {queue.queue_number}."
        )

        try:
            send_message(
                body=message,
                from_=frappe.db.get_single_value("Appointments Twilio Settings", "from_phone_number"),
                to=contact_number
            )
        except Exception as e:
            frappe.log_error(f"SMS sending failed for Queue {queue.name}: {str(e)}")




def _time_to_td(t):
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)

def send_absent_after_shift_sms():
    today = datetime.now().date()
    now = datetime.now()
    current_td = _time_to_td(now.time())

    has_contact_col = frappe.db.has_column("Appointment Queue", "contact_number")
    fields = ["name", "patient_name", "clinic", "shift", "doctor", "date"]
    if has_contact_col:
        fields.append("contact_number")

    queues = frappe.get_all(
        "Appointment Queue",
        filters={"status": "Absent", "absent_sms_sent": 0, "date": ["<=", today]},
        fields=fields,
        ignore_permissions=True,
        limit_page_length=0,
    )

    for q in queues:
        shift = frappe.db.get_value(
            "Schedule Shift", q.shift, ["start_time", "end_time", "title"], as_dict=True
        )
        if not shift or not shift.get("end_time"):
            frappe.log_error(f"No end_time on shift for Appointment Queue {q.name}", "Absent SMS")
            continue

        end = shift["end_time"]
        end_td = end if isinstance(end, timedelta) else _time_to_td(end)

        shift_over = (q.date < today) or (q.date == today and current_td >= end_td)
        if not shift_over:
            continue

        aq_contact = getattr(q, "contact_number", None) if has_contact_col else None
        contact_number = aq_contact or frappe.db.get_value(
            "Appointment",
            {
                "date": q.date,
                "shift": q.shift,
                "clinic": q.clinic,
                "doctor": q.doctor,
                "patient_name": q.patient_name,
            },
            "contact_number",
        )
        if not contact_number:
            frappe.log_error(f"No contact number for Appointment Queue: {q.name}", "Absent SMS")
            continue

        doctor_name = frappe.db.get_value("Doctor", q.doctor, "full_name")
        if not doctor_name:
            names = frappe.db.get_value("Doctor", q.doctor, ["first_name", "last_name"])
            if isinstance(names, (list, tuple)):
                doctor_name = " ".join([n for n in names if n])
        doctor_name = doctor_name or str(q.doctor)

        message = (
            f"Hi {q.patient_name}, you were marked absent for your appointment at {q.clinic} "
            f"on {q.date} ({shift.get('title') or ''}) with Dr. {doctor_name}. "
            f"Reply or call to reschedule."
        )

        try:
            send_message(
                body=message,
                from_=frappe.db.get_single_value("Appointments Twilio Settings", "from_phone_number"),
                to=contact_number,
            )
            frappe.db.set_value("Appointment Queue", q.name, "absent_sms_sent", 1, update_modified=False)
            if frappe.db.has_column("Appointment Queue", "absent_sms_sent_on"):
                frappe.db.set_value("Appointment Queue", q.name, "absent_sms_sent_on", now, update_modified=False)

            frappe.logger("AbsentSMS").info(f"Sent absent SMS for {q.name} to {contact_number}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed Absent SMS for Queue {q.name}")



def send_absent_after_shift_sms_at_3pm():
    now = datetime.now()

    if now.hour != 15 or now.minute != 23:
        return

    today = now.date()
    current_td = _time_to_td(now.time())

    has_contact_col = frappe.db.has_column("Appointment Queue", "contact_number")
    fields = ["name", "patient_name", "clinic", "shift", "doctor", "date"]
    if has_contact_col:
        fields.append("contact_number")

    queues = frappe.get_all(
        "Appointment Queue",
        filters={"status": "Absent", "absent_sms_sent": 0, "date": ["<=", today]},
        fields=fields,
        ignore_permissions=True,
        limit_page_length=0,
    )

    for q in queues:
        shift = frappe.db.get_value(
            "Schedule Shift", q.shift, ["start_time", "end_time", "title"], as_dict=True
        )
        if not shift or not shift.get("end_time"):
            frappe.log_error(f"No end_time on shift for Appointment Queue {q.name}", "Absent SMS")
            continue

        end = shift["end_time"]
        end_td = end if isinstance(end, timedelta) else _time_to_td(end)

        shift_over = (q.date < today) or (q.date == today and current_td >= end_td)
        if not shift_over:
            continue

        aq_contact = getattr(q, "contact_number", None) if has_contact_col else None
        contact_number = aq_contact or frappe.db.get_value(
            "Appointment",
            {
                "date": q.date,
                "shift": q.shift,
                "clinic": q.clinic,
                "doctor": q.doctor,
                "patient_name": q.patient_name,
            },
            "contact_number",
        )
        if not contact_number:
            frappe.log_error(f"No contact number for Appointment Queue: {q.name}", "Absent SMS")
            continue

        doctor_name = frappe.db.get_value("Doctor", q.doctor, "full_name")
        if not doctor_name:
            names = frappe.db.get_value("Doctor", q.doctor, ["first_name", "last_name"])
            if isinstance(names, (list, tuple)):
                doctor_name = " ".join([n for n in names if n])
        doctor_name = doctor_name or str(q.doctor)

        message = (
            f"Hi {q.patient_name}, you were marked absent for your appointment at {q.clinic} "
            f"on {q.date} ({shift.get('title') or ''}) with Dr. {doctor_name}. "
            f"Reply or call to reschedule."
        )

        try:
            send_message(
                body=message,
                from_=frappe.db.get_single_value("Appointments Twilio Settings", "from_phone_number"),
                to=contact_number,
            )
            frappe.db.set_value("Appointment Queue", q.name, "absent_sms_sent", 1, update_modified=False)
            if frappe.db.has_column("Appointment Queue", "absent_sms_sent_on"):
                frappe.db.set_value("Appointment Queue", q.name, "absent_sms_sent_on", now, update_modified=False)

            frappe.logger("AbsentSMS").info(f"Sent absent SMS for {q.name} to {contact_number}")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed Absent SMS for Queue {q.name}")
