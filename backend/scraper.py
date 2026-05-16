import csv
import os
import requests
import base64
from dotenv import load_dotenv
from pymongo import MongoClient
from database import get_db
from facial_recognition_module import get_face_encoding

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
mongo_client = MongoClient(MONGO_URL)
user_db = mongo_client["user"] 
image_collection = user_db["images"]

def scrape():
    db = get_db()   

    cursor = db.cursor()
    
    try:
        with open("batch_data.csv", newline="", encoding="utf-8") as f:
            file_content = csv.DictReader(f)
            for row in file_content:
                uid = row["uid"]
                name = row["name"]
                website_url = row["website_url"]
                image_url = f"https://{website_url}/images/pfp.jpg"

                try:
                    response = requests.get(image_url, timeout=5)

                    if response.status_code != 200:
                        print(f"[SKIP] {name} - status {response.status_code}")
                        continue
                    
                    image_data = base64.b64encode(response.content).decode("utf-8")
                    img_encoding = get_face_encoding(image_data)

                except Exception as e:
                    print(f"[SKIP] {name} - {e}")
                    continue

                try:
                    cursor.execute(
                        "INSERT INTO users (uid, name, elo_rating, is_online) VALUES (%s, %s, %s, %s) ON CONFLICT (uid) DO NOTHING",
                        (uid, name, 1200, 0)
                    )
                    db.commit()

                except Exception as e:
                    print(f"[DB ERROR] {name} - {e}")
                    continue

                try:
                    image_collection.update_one(
                        {"uid": uid},
                        {"$set": {"uid": uid, "image": image_data, "encoding":img_encoding.tolist() if img_encoding is not None else None}},
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