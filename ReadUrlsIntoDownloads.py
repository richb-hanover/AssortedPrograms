import os
import requests

THIS REALLY DOESN'T WORK.
Just build a shell script by scraping each of the pages, and editing out irrelevant stuff

def download_files(url_list):
    for url in url_list:
        response = requests.get(url,allow_redirects=True)
        filename = os.path.basename(url)
        with open(f"/Users/richb/Downloads/%s" % filename, "wb") as f:
            f.write(response.content)

url_list = [
"https://www.lymenh.gov/office-select-board-select-board/minutes/select-board-minutes-3"
]

download_files(url_list)
