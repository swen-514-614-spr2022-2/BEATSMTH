"""
TheNexusAvenger

Modified 3/22/22 for AWS compatability
Utility for interacting with Beat Saver.
"""

import json
import csv
import requests
import time
import wget
import os

class Page:
    def __init__(self):
        self.songs = []
        self.page = None



"""
Makes a request to Beat Saver.
"""
def get(url, host = "www.beatsaver.com"):
    # Get the request emulating the Chrome browser.
    # An account and API key aren't required in this case.
    response = requests.get(url, headers={
            "Host": host,
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "sec-ch-ua": "\"Chromium\";v=\"92\", \" Not A;Brand\";v=\"99\", \"Google Chrome\";v=\"92\"",
            "sec-ch-ua-mobile": "?0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
        }).content

    # Try to parse the JSON response and re-run if it is requires a retry.
    try:
        responseString = response.decode()
        responseJson = json.loads(responseString)
        if "identifier" in responseJson and responseJson["identifier"] == "RATE_LIMIT_EXCEEDED":
            delay = (responseJson["resetAfter"]/1000) + 1
            print("Rate limit reached. Retrying in " + str(delay) + " seconds.")
            time.sleep(delay)
            return get(url)
    except Exception:
        pass

    # Return the response contents.
    return response

"""
Returns the data for a page.
"""
def getPage(pageNumber):
    # Get the page data.
    pageData = json.loads(get("https://www.beatsaver.com/api/search/text/" + str(pageNumber) + "?sortOrder=Rating").decode())

    # Parse and return the page.
    page = Page()
    page.page = pageNumber
    for songData in pageData["docs"]:
        key = songData["id"]

        page.songs.append(key)
    return page

def writeToCSV(url):
    with open('urls.csv','a') as fd:
        writer = csv.writer(fd)
        writer.writerow([url])
    

def urlExists(url):
    try:
        with open("urls.csv", "r") as f:
            csvreader = csv.reader(f, delimiter=",")
            for row in csvreader:
                if url in row:
                    return True
    except:
        open('urls.csv', 'w+')

   

def getMap(key):
    songData = json.loads(get("https://www.beatsaver.com/api/maps/id/" + key).decode())
    url = songData["versions"][0]["downloadURL"]

    if not urlExists(url):
        writeToCSV(url)
        # time remaining 
        for remaining in range(10, 0, -1):
            time.sleep(1)
            if(remaining == 10):
                if not os.path.exists('beat-saver-zips'):
                    os.mkdir('beat-saver-zips')
                    wget.download(url, out="beat-saver-zips")
                    print("\n")
                else:
                    wget.download(url, out="beat-saver-zips")
                    print("\n")

    

def main():

    #range of pages to visit and download from
    x = range(0,15)

    for n in x:
        print(n)
        page_items = getPage(n)
        print(page_items.songs)
        #page_items = getPage("1")
        for keys in page_items.songs:
            getMap(keys)    

if __name__ == "__main__":
    main()