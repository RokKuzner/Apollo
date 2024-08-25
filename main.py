from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

import google_auth_oauthlib.flow
import googleapiclient.discovery

import re

class RadioKoperMusicExtracter():
  def __init__(self) -> None:
    self.WAITER_TIMEOUT = 5
    self.BETWEEN_WAIT = 0.5
    self.INITIAL_WAIT = 2

    self.RED_ANSI = "\033[31m"
    self.GREEN_ANSI = "\033[32m"
    self.RESET_ANSI = "\033[0m"

  def extract_yt_search_urls(self, days_to_extract:int) -> list[str]:
    print(f"{self.RED_ANSI}Starting extract_yt_search_urls{self.RESET_ANSI}")

    url = "https://radio.rtvslo.si/glasbenisos/?chid=5&lang=0#pageone"

    #Set up the driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    urls = []

    #Get the page
    driver.get(url)
    time.sleep(self.INITIAL_WAIT)

    #Get all day elements
    days = driver.find_elements("css selector", ".page_one_days")

    #Check if days_to_extract is int
    if type(days_to_extract) != int:
      raise Exception(f"Days to extract is {type(days_to_extract)}. Only {int} allowed.")
    #Check if days_to_extract is greater than 0 and not more than the number of avalible days to extract
    if days_to_extract <= 0 or days_to_extract > len(days):
      raise Exception(f"Days to extract out of range. Value for days to extract must be greather than 0 and not more than the number of avalible days to extract (currently {len(days)}).") 

    #Loop through all days
    for day in days[:days_to_extract]:
      day.click() #Click on the day

      #Get all hours in that day and loop through tem
      time.sleep(self.BETWEEN_WAIT)
      hours = driver.find_elements("css selector", ".page_one_hours")
      for hour in hours:
        hour.click() #Click on the hour

        #Get all songs in that hour and loop through them
        time.sleep(self.BETWEEN_WAIT)
        songs = driver.find_elements("css selector", "tbody tr td a")
        for song in songs:
          urls.append(song.get_attribute("href"))

        driver.execute_script('document.querySelector(".ui-header a.ui-btn-left").click()') #Go one page back
        time.sleep(self.BETWEEN_WAIT)

      driver.execute_script('document.querySelector(".ui-header a.ui-btn-left").click()') #Go one page back
      time.sleep(self.BETWEEN_WAIT)


    #Quit the driver
    driver.quit()

    #Return urls
    return urls
  
  def extract_yt_video_urls(self, days_to_extract:int, yt_search_urls=[]) -> list[str]:
    if not yt_search_urls:
      yt_search_urls = self.extract_yt_search_urls(days_to_extract)

    yt_video_urls = []

    print(f"{self.RED_ANSI}Starting extract_yt_video_urls{self.RESET_ANSI}")

    #Set up the driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    waiter = WebDriverWait(driver, 3)

    for indx, search_url in enumerate(yt_search_urls):
      print(f"{self.GREEN_ANSI}{indx+1}/{len(yt_search_urls)}{self.RESET_ANSI}")

      try:
        driver.get(search_url)
      except Exception as e:
        print(f"Could not get {search_url}. Error:", e)

      first_video_thumbnail_anchor = waiter.until(EC.presence_of_element_located(("css selector", "#contents ytd-video-renderer #dismissible.ytd-video-renderer ytd-thumbnail.ytd-video-renderer a")))

      yt_video_urls.append(first_video_thumbnail_anchor.get_attribute("href"))

    #Quit driver
    driver.quit()

    #Return urls
    return yt_video_urls

class YoutubeInteracter():
  def __init__(self) -> None:
    self.scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    self.secrets_file = "client_secrets.json"

    self.flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(self.secrets_file, self.scopes)
    self.credentials = self.flow.run_local_server()

    self.youtube = googleapiclient.discovery.build("youtube", "v3", credentials=self.credentials)

  def create_playlist(self, playlist_title:str) -> str:
    new_playlist_request = self.youtube.playlists().insert(
      part="snippet,status",
      body={
        "snippet": {
          "title": playlist_title
        },
        "status": {
          "privacyStatus": "public"
        }
      }
    )
    new_playlist_response = new_playlist_request.execute()

    playlist_id = new_playlist_response["id"]
    return playlist_id
  
  def add_videos_to_playlist(self, video_ids:list[str], playlist_id:str):
    for video_id in video_ids:
      request = self.youtube.playlistItems().insert(
        part='snippet',
        body={
          "snippet": {
            "playlistId": playlist_id,
            "resourceId":{
              "kind": "youtube#video",
              "videoId": video_id
            }
          }
        }
      )
      response = request.execute()

class Apollo():
  def __init__(self) -> None:
    self.radio_koper_music_interacter = RadioKoperMusicExtracter()
    self.youtube_interacter = YoutubeInteracter()

    self.RED_ANSI = "\033[31m"
    self.RESET_ANSI = "\033[0m"

  def run(self, days_to_extract:int):
    yt_video_urls = self.radio_koper_music_interacter.extract_yt_video_urls(days_to_extract)

    yt_video_url_pattern = re.compile(r"(?:https:\/\/www\.youtube\.com\/watch\?v=)(?P<id>[a-zA-Z0-9\-_]{11})(?:\&.*)?")
    video_ids = []
    for yt_video_url in yt_video_urls:
      match = re.search(yt_video_url_pattern, yt_video_url)
      if match:
        video_ids.append(match.group("id"))
      else:
        print(f"{self.RED_ANSI}Match for {yt_video_url} not found!{self.RESET_ANSI}")
