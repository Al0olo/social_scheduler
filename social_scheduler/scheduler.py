import frappe
from datetime import datetime
import requests
@frappe.whitelist(allow_guest=True)
def schedule_posts():
    posts = frappe.get_all(
        "Social Post",
        filters={
            "status": "Scheduled",
            "scheduled_time": ["<=", datetime.now()]
        },
        fields=["name", "content", "platforms"]
    )
    
    for post in posts:
        try:
            platform = frappe.get_doc("Social Platform", post.platforms)
            
            if platform.platform == "LinkedIn":
                post_to_linkedin(post.content, platform.access_token)
            elif platform.platform == "Twitter":
                post_to_twitter(post.content, platform.access_token)
            
            doc = frappe.get_doc("Social Post", post.name)
            
            doc.status = "Posted"
            doc.save()
        except Exception as e:
            frappe.log_error(f"Failed to post {post.name}: {str(e)}")
            # doc.status = "Failed"
            # doc.save()

def post_to_linkedin(content, access_token):
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "author": "urn:li:person:{USER_ID}",  # Replace with actual user ID
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

def post_to_twitter(content, access_token):
    url = "https://api.twitter.com/2/tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "text": content
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()