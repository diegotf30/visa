from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from selenium import webdriver
import smtplib, ssl
import traceback
import locale
import time
import json


def parse_datestring(date: str):
	date = date.replace('Cita Consular: ', '')
	locale.setlocale(locale.LC_ALL, 'es_MX')  # WARNING: DANGEROUS
	return datetime.strptime(date[:date.index(':') + 3], '%d %B, %Y, %H:%M')

def send_email(to: str, content: str):
	sender_email = CONFIG_JSON['sender_email']
	password = CONFIG_JSON['sender_email_password']

	msg = MIMEMultipart("alternative")
	msg['Subject'] = 'Citas para la visa'
	msg['X-Priority'] = '1'
	msg['From'] = sender_email
	msg['To'] = to
	msg.attach(MIMEText(content, "plain"))

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL('smtp.gmail.com', port=465, context=context) as server:
		server.login(sender_email, password)
		server.sendmail(sender_email, to, msg.as_string())
	print('sent email to', to)

def scroll_until_available_day(ff: webdriver.Firefox) -> datetime:
	time.sleep(1)
	calendar = ff.find_element_by_id('ui-datepicker-div')
	for _ in range(12): # Check next 12 months
		avail_dates = calendar.find_elements_by_css_selector('td[data-handler="selectDay"]')
		if len(avail_dates) == 0:
			calendar.find_element_by_css_selector('a[title="Next"]').click()
			continue
		else:
			selected_day = avail_dates[0]
			appointment = datetime(int(selected_day.get_attribute('data-year')),
							int(selected_day.get_attribute('data-month')) + 1,
							int(selected_day.text))
			selected_day.click()
			return appointment
	return None

def book_appointment(ff: webdriver.Firefox, appointment_type: str, desired_place: str) -> datetime:
	# Select place
	places_dropdown = ff.find_element_by_id(f'appointments_{appointment_type}_appointment_facility_id')
	places_dropdown.click()
	available_places = places_dropdown.find_elements_by_tag_name('option')
	[place.click() for place in available_places if place.text == desired_place]
	time.sleep(3)

	# Select date (scroll thru calendar)
	ff.find_element_by_id(f'appointments_{appointment_type}_appointment_date').click()
	date = scroll_until_available_day(ff)
	if date is None:
		return None

	# Select time
	times_dropdown = ff.find_element_by_id(f'appointments_{appointment_type}_appointment_time')
	times_dropdown.click()
	selected_time = times_dropdown.find_elements_by_tag_name('option')[1] # First available timeslot
	selected_time.click()
	hour, minutes = map(int, selected_time.text.split(':'))
	return date + timedelta(hours=hour, minutes=minutes)

def look_for_appointments(ff: webdriver.Firefox, in_place: str):
	ff.get(URL)
	# SIGN IN
	ff.find_element_by_id('user_email').send_keys(CONFIG_JSON['visa_email'])
	ff.find_element_by_id('user_password').send_keys(CONFIG_JSON['visa_email_password'])
	ff.find_elements_by_class_name('icheckbox')[0].click()
	ff.find_element_by_name('commit').click()
	time.sleep(3) # Wait for load

	# GET SCHEDULED APPT
	scheduled_consulate_appointment_str = ff.find_element_by_css_selector('p[class="consular-appt"]').text
	scheduled_consulate_appointment = parse_datestring(scheduled_consulate_appointment_str)

	# GO TO RESCHEDULE PAGE
	ff.find_element_by_link_text('Continuar').click()
	ff.find_element_by_link_text('Reprogramar cita').click()
	ff.find_elements_by_link_text('Reprogramar cita')[1].click()

	# LOOK FOR AVAILABLE DATES
	consulate_appointment = book_appointment(ff, 'consulate', in_place)
	if consulate_appointment is None:
		print('Could not find available day')
		return

	print(consulate_appointment, 'appointment found for consulate', in_place, end=' ')
	if consulate_appointment < scheduled_consulate_appointment:
		print('**SCHEDULED**')
		asc_appointment = book_appointment(ff, 'asc', f'{in_place} ASC')
		print(asc_appointment, f'scheduled for ASC appointment, {in_place} ASC')
		ff.find_element_by_name('commit').click()
		ff.find_element_by_link_text('Confirmar').click()
		send_email(to=CONFIG_JSON['notification_email'], content=f'booked appointments! consulate: {consulate_appointment} asc: {asc_appointment}')
	else:
		print(f' | was after scheduled appt ({scheduled_consulate_appointment})')

if __name__ == '__main__':
	URL = 'https://ais.usvisa-info.com/es-mx/niv/users/sign_in'
	with open('config.json', 'r') as f:
		CONFIG_JSON = json.load(f)

	while True:
		ff_opts = webdriver.FirefoxOptions()
		ff_opts.add_argument('--headless')
		ff = webdriver.Firefox(options=ff_opts)
		try:
			look_for_appointments(ff, in_place='Monterrey')
		except (NoSuchElementException, ElementNotInteractableException) as e:
			print(e, end='')
		except KeyboardInterrupt:
			ff.close()
			break
		except Exception as e:
			print(traceback.format_exc())

		ff.close()
		time.sleep(5 * 60) # 5 min