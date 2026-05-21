import os
import requests
import urllib.parse
import re  # Regex for filename detection
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ==========================================
# 👇 STRICT CONFIGURATION (Education Mode) 👇
# ==========================================

TOPIC_NAME = "Education_Motivation"

CONFIG = {
    # 1. Category Setting (STRICTLY Education)
    "category_id": "27",  
    
    # 2. AI Prompts (No Stars, No Hashtags in text)
    "title_prompt": "Write a short viral motivational quote video title in English under 60 characters. No hashtags. No quotes. No emoji.",
    "desc_prompt": "Write a deep, educational and inspiring explanation (max 2 sentences) about the importance of success and learning. Plain text only. No stars. No hashtags inside text.",
    
    # 3. SEO Settings
    "seo_hashtags": "#education #educationalvideo #learning #knowledge #facts #lifelessons #wisdom #motivation #inspiration #selfimprovement #successmindset #studytips #growthmindset #personaldevelopment #dailymotivation #positivemindset #studentlife #motivationalvideo #educationalshorts #ytshorts #Education #Motivation #Learning #Success #StudyMotivation #Wisdom #Shorts #Facts #Education #EducationalVideo #Facts #Inspiration #Knowledge #Learning #LifeLessons #Motivation #SelfImprovement #StudyTips #SuccessMindset #Wisdom #USA #USAEducation #ViralUSA #EnglishQuotes #GlobalLearning",
    
    # 4. Tags List (Targeting USA Audience)
    "tags": [
        "education", "educationalvideo", "learning", "knowledge", "facts", 
        "lifelessons", "wisdom", "motivation", "inspiration", "selfimprovement", 
        "successmindset", "studytips", "growthmindset", "personaldevelopment", 
        "dailymotivation", "positivemindset", "studentlife", "motivationalvideo", 
        "educationalshorts", "ytshorts", "Education", "Motivation", "Learning", 
        "Success", "StudyMotivation", "Wisdom", "Shorts", "Facts", "Education", 
        "EducationalVideo", "Facts", "Inspiration", "Knowledge", "Learning", 
        "LifeLessons", "Motivation", "SelfImprovement", "StudyTips", "SuccessMindset", 
        "Wisdom", "USA", "United States", "American Students", "US Trending", 
        "Global Motivation", "English Language", "Ivy League Vibes", "Success USA"
    ]
}

CHANNEL_CUSTOM_NAME = "My Education Channel"

# ==========================================
# 👆 CONFIGURATION END 👆
# ==========================================

def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not client_id or not refresh_token:
        raise ValueError("Secrets missing! Check GitHub Settings.")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    return build("youtube", "v3", credentials=creds)

def ask_pollinations_ai(prompt):
    """AI se unique text generate karna"""
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://text.pollinations.ai/{encoded_prompt}?seed={os.urandom(4).hex()}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return None
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def should_replace_title(title):
    """
    Check karta hai ki kya Title badalne ki zarurat hai.
    Agar title filename jaisa dikhta hai to True return karega.
    """
    # 1. Agar title bahut chhota hai
    if len(title) < 5:
        return True
    
    # 2. Agar title mein 'Untitled' ya 'Upload' word hai
    if "untitled" in title.lower() or "upload" in title.lower():
        return True
        
    # 3. Agar title mein Spaces nahi hain (e.g., VID_20250207) -> Filename hai
    if " " not in title:
        return True
        
    # 4. Agar title mein Date format hai (e.g., 2025-02-07)
    if re.search(r'\d{4}-\d{2}-\d{2}', title):
        return True
        
    return False

def send_telegram_alert(video_id, channel_name):
    """
    Telegram Message Format:
    Channel Name (Big Red)
    Message
    Category
    Link
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return

    video_link = f"https://youtu.be/{video_id}"
    
    # Red & Bold Simulation using Emoji and HTML
    formatted_name = f"<b>🔴 {channel_name.upper()} 🔴</b>"

    message = (
        f"{formatted_name}\n"
        f"Message: Upload Successful\n"
        f"Category: Education\n"
        f"{video_link}"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id, 
        'text': message, 
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    requests.post(url, json=payload)

def main():
    try:
        print(f"--- STARTING AUTOMATION ---")
        youtube = get_youtube_service()
        
        # 1. Connect to Channel & Get Uploads Playlist
        channel_response = youtube.channels().list(
            part="snippet,contentDetails",
            mine=True
        ).execute()
        
        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        print(f"✅ Channel Connected: {channel_response['items'][0]['snippet']['title']}")

        # 2. Get Recent Videos (Includes Private/Unlisted)
        # Increased maxResults to 50 to scan more videos at once
        playlist_request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50  
        )
        playlist_response = playlist_request.execute()
        
        videos_processed = 0
        
        # 3. Find and loop through ALL Unlisted/Private Videos
        for item in playlist_response.get("items", []):
            vid_id = item["contentDetails"]["videoId"]
            
            vid_request = youtube.videos().list(
                part="snippet,status",
                id=vid_id
            )
            vid_response = vid_request.execute()
            
            if not vid_response["items"]:
                continue
                
            video_data = vid_response["items"][0]
            privacy = video_data["status"]["privacyStatus"]
            
            # Agar video private ya unlisted hai to process karega
            if privacy in ["private", "unlisted"]:
                snippet = video_data["snippet"]
                print(f"\n--- Target Found: {vid_id} | Current Status: {privacy} ---")
                
                # --- AI & CONTENT LOGIC ---
                
                # A) TITLE GENERATION
                current_title = snippet["title"]
                new_title = current_title
                
                if should_replace_title(current_title):
                    print("Generating new AI Title...")
                    ai_title = ask_pollinations_ai(CONFIG["title_prompt"])
                    if ai_title:
                        new_title = ai_title.replace('"', '').replace("'", "")
                        if len(new_title) > 70: new_title = new_title[:67] + "..."
                else:
                    print("Keeping existing title.")
                
                # B) DESCRIPTION GENERATION
                print("AI Writing Description...")
                ai_desc = ask_pollinations_ai(CONFIG["desc_prompt"])
                if not ai_desc:
                    ai_desc = "Motivational video."
                    
                final_description = f"{ai_desc}\n\n{CONFIG['seo_hashtags']}"
                
                # C) TAGS LOGIC (SMART FIX)
                raw_tags = CONFIG["tags"]
                final_tags = []

                # Check: Agar tags ek hi string mein hain (space separated)
                if len(raw_tags) == 1 and " " in raw_tags[0]:
                    print("Fixing Tags format automatically...")
                    final_tags = [t.replace("#", "") for t in raw_tags[0].split() if t.strip()]
                else:
                    final_tags = raw_tags

                # Ensure Minimum Tags
                if len(final_tags) < 8:
                    final_tags.extend(["Viral", "Trending", "Must Watch", "New Video", "Shorts"])

                # Remove Duplicates & Limit to 30 tags
                final_tags = list(set(final_tags))[:30]
                print(f"Total Tags to Add: {len(final_tags)}")

                # --- UPDATE VIDEO ---
                update_body = {
                    "id": vid_id,
                    "snippet": {
                        "categoryId": CONFIG["category_id"],
                        "title": new_title,
                        "description": final_description,
                        "tags": final_tags, 
                        "channelTitle": snippet.get("channelTitle", CHANNEL_CUSTOM_NAME)
                    },
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False,
                        "embeddable": True,
                        "license": "youtube"
                    }
                }
                
                youtube.videos().update(
                    part="snippet,status",
                    body=update_body
                ).execute()
                
                print(f"SUCCESS: Video Public | Title: {new_title}")
                
                # Telegram Alert
                display_name = snippet.get("channelTitle", CHANNEL_CUSTOM_NAME)
                send_telegram_alert(vid_id, display_name)
                
                videos_processed += 1
        
        # Loop khatam hone ke baad summary
        if videos_processed == 0:
            print("No Unlisted/Private videos found.")
        else:
            print(f"\n--- AUTOMATION COMPLETED. Total {videos_processed} videos published. ---")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        
if __name__ == "__main__":
    main()
