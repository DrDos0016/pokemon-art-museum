import json
from pprint import pprint

import requests


URLS = {
    "base": "https://archiverse.guide/api/posts/"
}

COMMUNITIES = {
    "US": "14866558073457096100",
    "EU": "14866558073328768494",
    "JP": "14866558073315036717",
}

HEADERS = {
    "content-type": "application/json",
    "Accept": "application/json",
}

DAYS_IN_MONTH = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 31,
    10: 31,
    11: 30,
    12: 31,
}


def prepare_post(community, start_date, end_date, page=1):
    post = {
        "textSearch": "",
        "gameId": "",
        "titleId": "",
        "name": "",
        "screenName": "",
        "isDrawingOnly": False,
        "isScreenshotOnly": False,
        "orderByDateDescending": False,
        "reverse": False,
        "startDate": "{}T19:00:00.000Z",
        "endDate": "{}T19:00:00.000Z",
        "sortEmpathy": 0,
        "sortReplyCount": 0,
        "page": 1
    }

    post["gameId"] = community
    post["startDate"] = post["startDate"].format(start_date)
    post["endDate"] = post["endDate"].format(end_date)
    post["page"] = page

    return post


def main():
    community = COMMUNITIES["US"]
    start_date = "2015-08-01"
    end_date = "2015-08-31"
    page = 801
    running = True

    with open("/var/projects/pokemon_art_museum/output/us.dat", "w") as fh:
        while running:
            post = prepare_post(community, start_date, end_date, page)
            resp = requests.post(URLS["base"],
                                 data=json.dumps(post),
                                 headers=HEADERS)
            if resp.status_code == 200:
                data = resp.json()
            else:
                print("STATUS CODE", resp.status_code)
                #print(resp.text)
                input("HANGING ON PAGE: " + str(page))
                continue
            print(resp.status_code, "start", start_date, "end", end_date,
                  "currentPage", data["currentPage"], "pageCount",
                  data["pageCount"], "FirstVisible", data["firstRowOnPage"],
                  "LastVisible", data["lastRowOnPage"],
                  "RES", len(data["results"]))

            # Advance date if needed
            if len(data["results"]) != 20:
                page = 1
                y = int(start_date.split("-")[0])
                m = int(start_date.split("-")[1])

                m += 1
                if m > 12:
                    m = 1
                    y += 1
                    input("YEAR BREAK.")

                start_date = str(y) + "-" + ("0" + str(m))[-2:] + "-01"

                if m == 2 and y == 2016:
                        d = 29
                else:
                    d = ("0" + str(DAYS_IN_MONTH[m]))[-2:]
                end_date = str(y) + "-" + ("0" + str(m))[-2:] + "-" + d
            else:
                page += 1

            # Log the posts
            posts = data.get("results", [])
            for p in posts:
                if p.get("screenShotUri", "") != "":
                    fh.write(json.dumps(p) + "\n")
    return True


if __name__ == "__main__":
    main()
