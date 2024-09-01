import googleapiclient.errors
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

import google_auth_oauthlib.flow
import googleapiclient.discovery

import re
from datetime import datetime, timedelta
import pytz

class RadioKoperMusicExtracter():
  def __init__(self) -> None:
    self.WAITER_TIMEOUT = 5
    self.BETWEEN_WAIT = 0.5
    self.INITIAL_WAIT = 2

    self.RED_ANSI = "\033[31m"
    self.GREEN_ANSI = "\033[32m"
    self.RESET_ANSI = "\033[0m"

  def extract_yt_search_urls(self, day_to_extract:int) -> list[str]:
    print(f"{self.RED_ANSI}Starting extraction of youtube search urls{self.RESET_ANSI}")

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

    #Check if day_to_extract is int
    if type(day_to_extract) != int:
      raise Exception(f"Day to extract is {type(day_to_extract)}. Only {int} allowed.")
    #Check if day_to_extract is valid
    if day_to_extract < 0 or day_to_extract > len(days)-1:
      raise Exception(f"Day to extract is not valid.")

    #Loop through all days
    for day in [days[day_to_extract]]:
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
  
  def extract_yt_video_ids(self, day_to_extract:int, yt_search_urls=[]) -> list[str]:
    if not yt_search_urls:
      yt_search_urls = self.extract_yt_search_urls(day_to_extract)

    yt_video_ids = []

    print(f"{self.RED_ANSI}Starting extraction of youtube videos ids{self.RESET_ANSI}")

    #Set up the driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    waiter = WebDriverWait(driver, 3)

    yt_video_url_pattern = re.compile(r"(?:https:\/\/www\.youtube\.com\/watch\?v=)(?P<id>[a-zA-Z0-9\-_]{11})(?:\&.*)?")

    for indx, search_url in enumerate(yt_search_urls):
      print(f"{self.GREEN_ANSI}{indx+1}/{len(yt_search_urls)}{self.RESET_ANSI}")

      try:
        driver.get(search_url)
      except Exception as e:
        print(f"Could not get {search_url}. Error:", e)
        continue

      first_video_thumbnail_anchor = waiter.until(EC.presence_of_element_located(("css selector", "#contents ytd-video-renderer #dismissible.ytd-video-renderer ytd-thumbnail.ytd-video-renderer a")))
      video_url = first_video_thumbnail_anchor.get_attribute("href")

      #Extract the video id
      match = re.search(yt_video_url_pattern, video_url)
      if match:
        yt_video_ids.append(match.group("id"))
      else:
        print(f"{self.RED_ANSI}Match for {video_url} not found!{self.RESET_ANSI}")
        continue

    #Quit driver
    driver.quit()

    #Return urls
    return yt_video_ids

class YoutubeInteracter():
  def __init__(self) -> None:
    self.BLUE_ANSI = "\033[34m"
    self.RED_ANSI = "\033[31m"
    self.RESET_ANSI = "\033[0m"

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
    for indx, video_id in enumerate(video_ids):
      print(f"{self.BLUE_ANSI}{indx+1}/{len(video_ids)}{self.RESET_ANSI}")
      self.add_video_to_playlist(video_id, playlist_id)

  def add_video_to_playlist(self, video_id:str, playlist_id:str, attempt:int=1):
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
    try:
      response = request.execute()
    except Exception as e:
      if attempt > 3:
        print(f"{self.RED_ANSI}Could not add video '{video_id}' to playlist. Attempted {attempt-1} times.{self.RESET_ANSI}")
        return 1
      print(f"{self.RED_ANSI}Error while adding video id '{video_id}' to playlist. Attempt {attempt}. Attempting again...{self.RESET_ANSI}")
      time.sleep(0.5)
      self.add_video_to_playlist(video_id, playlist_id, attempt=attempt+1)

class Apollo():
  def __init__(self) -> None:
    self.RED_ANSI = "\033[31m"
    self.RESET_ANSI = "\033[0m"
    self.BLUE_ANSI = "\033[34m"

  def run(self, day_to_extract:int):
    #Initialize RadioKoperMusicExtracter
    self.radio_koper_music_interacter = RadioKoperMusicExtracter()

    #Get youtube video ids of songs played by Radio Koper on the day "day_to_extract"
    video_ids = self.radio_koper_music_interacter.extract_yt_video_ids(day_to_extract)

    #Create playlist title
    cest = pytz.timezone("Europe/Berlin")
    cest_time = datetime.now(cest)
    day_to_extract_date = cest_time - timedelta(days=day_to_extract)
    playlist_title = f"Radio Koper Music from {day_to_extract_date.day}. {day_to_extract_date.month}. {day_to_extract_date.year}"

    #Initialize YoutubeInteracter
    self.youtube_interacter = YoutubeInteracter()

    #Create the playlist
    print(f"{self.BLUE_ANSI}Creating playlist '{playlist_title}'{self.RESET_ANSI}")
    playlist_id = self.youtube_interacter.create_playlist(playlist_title)
    print(f"{self.BLUE_ANSI}Playlist created{self.RESET_ANSI}")

    #Add videos to playlist
    print(f"{self.BLUE_ANSI}\nAdding videos to playlist...{self.RESET_ANSI}")
    self.youtube_interacter.add_videos_to_playlist(video_ids, playlist_id)