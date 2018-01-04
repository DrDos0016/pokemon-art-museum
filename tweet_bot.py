import json
import os
import random
import sys
import time
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from twitter import *

from secret import (TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                    TWITTER_OAUTH_TOKEN, TWITTER_OAUTH_SECRET)


SCRIPT_DIR = "/var/projects/pokemon_art_museum/"


def produce_image(url_component, category, timestamped=False):
    url = "https://web.archive.org/" + url_component
    resp = requests.get(url)

    if resp.status_code != 200:
        print("Could not get image: ", resp.status_code)
        return False

    print(resp.status_code)
    i = Image.open(BytesIO(resp.content)).convert("RGBA")
    temp = i.load()
    temp[0, 0] = (temp[0, 0][0], temp[0, 0][1], temp[0, 0][2], 254)
    if timestamped:
        filename = str(int(time.time())) + "-" + category + ".png"
    else:
        filename = category + ".png"
    i.save(os.path.join(SCRIPT_DIR, "output", filename))
    return True


def main():
    # Choose a community to feature
    communities = ["us", "eu", "jp"]
    today = datetime.now()
    index = int(today.strftime("%j")) % 3  # 0-2 based on day number
    community = communities[index]

    # DEBUG UNTIL ALL DATA IS COPIED
    community = "us-wip"

    # Grab a random row from the dataset
    with open(os.path.join(SCRIPT_DIR, "data", community + ".dat")) as fh:
        choices = fh.readlines()

        attempts = 1
        while attempts < 10:
            post = random.choice(choices)
            print(post)
            post = json.loads(post)
            print("Post Image", post["imageUri"])
            print("Post SCREENSHOT", post["screenShotUri"])

            date = datetime.fromtimestamp(post.get("postedDate", 0))
            date = datetime.strftime(date, "%b %d, %Y")
            artist = post.get("name", "UNKNOWN")
            yeahs = post.get("empathyCount", 0)
            yeah_word = "Yeah!" if yeahs == 1 else "Yeahs!"
            replies = post.get("replyCount", 0)
            reply_word = "reply" if replies == 1 else "replies"
            text = post.get("text")
            if text is None:
                text = ""
            url = "https://web.archive.org/https://miiverse.nintendo.net/posts/"
            url += post["id"]
            if text:
                text = '\n"' + text + '"'
            content = "{}. By: {}\n[{} {}] [{} {}] ({})\n{}{}".format(
                date, artist, yeahs, yeah_word, replies, reply_word,
                community.upper().split("-")[0], url, text
            )
            print(content)

            if len(content) > 280:
                print("TRUNCATED")
                content = content[:280]
                print(content)

            # Get the image(s)
            print("=" * 40)

            if post["screenShotUri"]:
                success = produce_image(post["screenShotUri"], "screenshot")
                if not success:
                    attempts += 1
                    continue
            if post["imageUri"]:
                success = produce_image(post["imageUri"], "comment")
                if not success:
                    attempts += 1
                    continue
            break

    # Tweet everything
    images = []
    tw_images = []

    if os.path.isfile(os.path.join(SCRIPT_DIR, "output", "screenshot.png")):
        ss_path = os.path.join(SCRIPT_DIR, "output", "screenshot.png")
        with open(ss_path, "rb") as image:
            images.append(image.read())
        os.remove(ss_path)

    if os.path.isfile(os.path.join(SCRIPT_DIR, "output", "comment.png")):
        comment_path = os.path.join(SCRIPT_DIR, "output", "comment.png")
        with open(comment_path, "rb") as image:
            images.append(image.read())
        os.remove(comment_path)

    t_up = Twitter(
        domain='upload.twitter.com',
        auth=OAuth(TWITTER_OAUTH_TOKEN, TWITTER_OAUTH_SECRET,
                   TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    )

    for image in images:
        tw_images.append(t_up.media.upload(media=image)["media_id_string"])
    t = Twitter(auth=OAuth(TWITTER_OAUTH_TOKEN, TWITTER_OAUTH_SECRET,
                           TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET))
    resp = t.statuses.update(status=content, media_ids=",".join(tw_images))
    print(resp)


if __name__ == "__main__":
    main()
