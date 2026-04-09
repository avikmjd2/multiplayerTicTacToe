import csv
import os
import requests
import base64
from dotenv import load_dotenv
from pymongo import MongoClient
from backend.database import get_db

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
mongo_client = MongoClient(MONGO_URL)
# ensured database names match validator.py ("user" db, "images" collection)
user_db = mongo_client["user"] 
image_collection = user_db["images"]

def scrape():
    db = get_db()   

    # this is basically sqlite 'connection' which avik wrote
    # and it gets data as dictionary instead of tuples

    cursor = db.cursor()
    
    try:
        with open("batch_data.csv", newline="", encoding="utf-8") as f:
            file_content = csv.DictReader(f)
            for row in file_content:
                uid = row["uid"]
                name = row["name"]
                website_url = row["website_url"]
                image_url = f"https://{website_url}/images/pfp.jpg"
                # now i will try to get image data from the image url using requests library


                try:
                    response = requests.get(image_url, timeout=5)
                    # try to get image but if not responding in less than 5 secs then skip

                    if response.status_code != 200:
                        # response code = 200 means all ok
                        print(f"[SKIP] {name} - status {response.status_code}")
                        continue
                    
                    # encode the image into utf-8 characters
                    image_data = base64.b64encode(response.content).decode("utf-8")


                except Exception as e:
                    print(f"[SKIP] {name} - {e}")
                    continue

                # SQLITE Update or insertion
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO users (uid, name, elo_rating, is_online) VALUES (?, ?, ?, ?)",
                        (uid, name, 1200, 0)
                    )
                    db.commit()
                    # basically Ctrl + S for the dtabase (SQLITE one)

                except Exception as e:
                    print(f"[SQLITE ERROR] {name} - {e}")
                    continue

                # MongoDB Update and insertion = upsertion
                try:
                    image_collection.update_one(
                        {"uid": uid},
                        {"$set": {"uid": uid, "image": image_data}},
                        upsert=True
                    )
                except Exception as e:
                    print(f"[MONGO ERROR] {name} - {e}")
                    continue

                print(f"[OK] Saved {name} to both databases.")
                
    except FileNotFoundError:
        print("[ERROR] batch_data.csv not found.")
    finally:
        db.close()
        print("[DONE] Scraping process finished.")

if __name__ == '__main__':
    scrape()