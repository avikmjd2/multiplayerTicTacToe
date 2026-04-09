import csv
import os
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from database import get_db
import base64

load_dotenv
MONGO_URL = os.getenv("MONGO_URL");

mongo_client = MongoClient(MONGO_URL)
arena_db = mongo_client["arena"]
image_list = arena_db["images"]

def scrape():

    db = get_db()   # this is basically sqlite 'connection' which avik wrote
                    # and it gets data as dictionary instead of tuples
    cursor = db.cursor()

    with open("batch_data.csv", newline="", encoding="utf-8") as f:
        file_content = csv.DictReader(f)
        for row in file_content:
            uid = row["uid"]
            name = row["name"]
            website_url = row["website_url"]
            image_url = f"https://{website_url}/images/pfp.jpg"

            # now i will try to get image data from the image url using requests library

            response = requests.get(image_url, timeout=5)
            # try to get image but if not responding in less than 5 secs then skip

            image_data = base64.b64encode(response.content).decode("utf-8")
            # encode the image into utf-8 characters

            cursor.execute(
                "INSERT OR IGNORE INTO users (uid, name) VALUES (?, ?)",
                (uid, name)
            )
            db.commit()
            # basically Ctrl + S for the dtabase (SQLITE one)

            # MongoDB Updation + INSERTION
            image_list.update_one(
                {"uid": uid},
                {"$set": {"uid": uid, "image": image_data}},
                upsert=True
            )
            
            print(f"Successfully saved {name} to both databases.\n")

    db.close()
    print("All rows processed successfully.")

if __name__=='__main__':
    scrape()