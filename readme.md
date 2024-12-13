# What Is Apollo
Apollo is an app that extracts song titles from songs that played on a specific day on Radio Koper, gets the youtube video id of each song's youtube video and adds those videos to a playlist on your youtube channel.

# Instalation
### Setting Up The YouTube Data API and Credentials
> [!WARNING]
> Do not skip this step of the app won't work.

To set up the API and credentials follow this steps:

1. Create your own **project in Google Cloud Console** (now called Google Cloud Platform).
2. Enable YouTube Data API v3 for your project
3. Create credentials
3. Download credentials in **JSON** format under "Credentials -> your_client_name -> Client Secrets -> Client Secret -> the download button on the right"
4. Rename the downloaded file to **"client_secrets.json" and add it to the /secrets** directory relative to the project folder (the /secrets directory might not exist, if it doesn't then simply create it)

### Installing dependecies
This project's dependencies are:
- [Docker](https://docs.docker.com/get-started/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

# Usage
To start the app simply run `docker-compose build && docker-compose up` and watch the output in the console if you are later prompted to login.