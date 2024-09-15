from googleapiclient.http import MediaInMemoryUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI
import streamlit as st
import time
import json
import re

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = json.loads(st.secrets["service_account_info"])
PARENT_FOLER_ID = "12RWE1TVfEsjR_sX14JdzXYAM6idVeeZ1"

pattern = r'"location": "([^"]+)"'
pattern1 = r'("postImageUrl": ")([^"]+)(")'
urls = []

if 'txt' not in st.session_state:
    st.session_state.txt = None

if 'json' not in st.session_state:
	st.session_state.json = None

client = OpenAI(
  api_key = st.secrets["OPENAI_API_KEY"],
)

st.title("Generate your posts for your character!")

name = st.text_input("Choose a charcter: ")
post_count = st.number_input("How many posts do u want", min_value=1, max_value=10, value=1, step=1)
places_count = st.number_input("how many places do u wanna go", min_value=1, max_value=5, value=3, step=1)
s_city = st.text_input("any specify city u want to go, leave blank if no")
others = st.text_input("any special requirements, leave blank if no")
if s_city:
	city = "please include " + s_city + " in one of the post"
else:
	city = ""

if st.button("Generate", type="primary"):
	json_response = client.chat.completions.create(

		model = "gpt-4o-mini",
		messages = [
		{
		"role":"system",
		"content":f"""you are {name}, if {name} has deceased, you are a time traveller, else you are a parody of {name}
		you are a Instagram influencer that likes to share your trips
		strictly provide a json format answer without any comments
		"""
		},
		{
		"role":"user",
		"content": f"""pls generate the account with {post_count} post/s, each post will include a city, and each city consists of {places_count} places you've visited 
		bring out the characteristic of {name} in your tone
		{city}
		{others}
		replace the word 'String' with information: 
		User(name: String, selfIntro: String, profileImageUrl: String, backgroundImageUrl: String)
		Post(title: String, content: String, trip: Trip, location: String<city>, postImageUrl: String)
		Trip(title: String, overallNotes: String, extraNotes: Map<noteTitle: String, noteContent: String>, places: List<place>)
		Place(name: String, notes: String, tipsNtricks: String)"""
		}
		],
		response_format={"type": "json_object"}
	)
	str_answer = json_response.choices[0].message.content.strip()
	

	cities = re.findall(pattern, str_answer)

	for city in cities:

		img_response = client.images.generate(
			model = "dall-e-3",
			prompt = f"generate a realistic Instagram vibe travel photo at {city} without people and brings out the art style and the characteristic of {city}",
			size = "1024x1024",
			quality = "standard",
			)

		urls.append(img_response.data[0].url)

	def replace_urls(match):
		global url_index
		replacement = f'"postImageUrl": "{urls[url_index]}"'
		url_index += 1
		return replacement

	url_index = 0
	pattern2 = r'"postImageUrl":\s*"https://[^"]*"'
	str_answer = re.sub(pattern2, replace_urls, str_answer)
	json_answer = json.loads(str_answer)
	st.session_state.json = json_answer

	txt_response = client.chat.completions.create(

			model = "gpt-4o-mini",
			messages = [
			{
			"role":"system",
			"content":"your are to beautify the data into readable article format"
			},
			{
			"role":"user",
			"content": f"{str_answer}"
			}
			],
		)
	
	txt = txt_response.choices[0].message.content.strip()
	st.session_state.txt = txt
	st.markdown(st.session_state.txt)

if st.button("upload"):
	print(st.session_state.json)
	creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
	service = build('drive', 'v3', credentials=creds)
	json_data = json.dumps(st.session_state.json, indent=4).encode('utf-8')
	media = MediaInMemoryUpload(json_data, mimetype='application/json')
	file_metadata = {
  'name': f'{name}_{post_count}posts.json',
  'mimeType': 'application/json',
  'parents' : [PARENT_FOLER_ID]
	}
	file = service.files().create(
  body=file_metadata,
  media_body=media,
  fields='id'
	).execute()

	st.toast("uploaded")

st.button("Clear")
