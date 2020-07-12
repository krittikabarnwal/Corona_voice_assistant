import requests
import json
import pyttsx3 
import speech_recognition as sr 
import re
import threading 
import time

API_KEY="tT85yjr3NLqN"
PROJECT_TOKEN="t4KgTpGTGNFp"
RUN_TOKEN="tKz14pmQj1En"


class Data:

	def __init__(self, api_key, project_token):
		self.api_key=api_key
		self.project_token=project_token
		self.params={
				"api_key":self.api_key
					}
		self.data=self.get_data()


	def get_data(self):
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data=json.loads(response.text)
		return data


	def get_total_cases(self):
		data = self.data['Total'] 
		for content in data:
			if content['name']=="Coronavirus Cases:": 
				return content['value']
		return "0"


	def get_total_death(self):
		data = self.data['Total']
		for content in data:
			if content['name']=="Deaths:":
				return content['value']
		return "0"


	def get_country_data(self,country):
		data=self.data['country']
		for content in data:
			if content['name'].lower()==country.lower():
				return content
		return "No data"


	def get_list_of_countries(self):
		countries=[]
		for country in self.data['country']:
			countries.append(country['name'].lower())
		return countries


	def update_data(self):
			response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

			def poll():
				time.sleep(0.1)
				old_data = self.data
				while True:
					new_data = self.get_data()
					if new_data != old_data:
						self.data = new_data
						print("Data updated")
						break
					time.sleep(5)

			t = threading.Thread(target=poll)
			t.start()


def speak(text):
	engine= pyttsx3.init()
	engine.say(text)
	engine.runAndWait()

def get_audio():
	r=sr.Recognizer()
	with sr.Microphone() as source:
		audio=r.listen(source)
		said=""

		try:
			said=r.recognize_google(audio)
		except Exception as e:
			print("Exception: ",str(e))
	return said.lower()


def main():
	print("Started Program")
	data = Data(API_KEY, PROJECT_TOKEN)
	END_PHRASE = "stop"
	country_list = set(data.get_list_of_countries()) 

	TOTAL_PATTERNS = {
			re.compile("total [\w\s]+ cases [\w\s]"):data.get_total_cases,
			re.compile("[\w\s]+ total cases [\w\s]"): data.get_total_cases,
			re.compile("total [\w\s]+ deaths [\w\s]"): data.get_total_death,
			re.compile("total [\w\s]+ death [\w\s]"): data.get_total_death,
			re.compile("total deaths [\w\s]"): data.get_total_death
					}
	

	COUNTRY_PATTERNS = {
	                re.compile("[\w\s]+ new [\w\s]+"): lambda country: data.get_country_data(country)['new_cases'],
	                re.compile("[\w\s]+ active [\w\s]+"): lambda country: data.get_country_data(country)['active_cases'],
	                re.compile("[\w\s]+ recovered [\w\s]+"): lambda country: data.get_country_data(country)['recovered'],
			re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_death'],
			re.compile("[\w\s]+ death [\w\s]+"): lambda country: data.get_country_data(country)['total_death'],
			re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
					}
	

	UPDATE_COMMAND = "update"

	while True:
		print("Listening...")
		text = get_audio()
		print(text)
		result = None
		flag=0
		
		for pattern, func in COUNTRY_PATTERNS.items():
			if pattern.match(text):
				words = set(text.split(" "))
				for country in country_list:
					if country in words:
						result = func(country)
						flag=1
						break
				if flag==1:
					break
		

		if flag==0:
			for pattern,func in TOTAL_PATTERNS.items():
				if pattern.match(text):
					result = func()
					break

		if text == UPDATE_COMMAND:
			result = "Data is being updated. This may take a moment!"
			data.update_data()

		if result:
			speak(result)
			print(result)

		if text.find(END_PHRASE) != -1:  # stop loop
			print("Exit")
			break

main()

