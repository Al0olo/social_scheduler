import frappe
import requests
from urllib.parse import urlencode
@frappe.whitelist(allow_guest=True)
def get_linkedin_auth_url():
    settings = frappe.get_single("Social Settings")
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": "w_member_social",
        "state": "linkedin"
    }
    return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

@frappe.whitelist(allow_guest=True)
def get_twitter_auth_url():
    settings = frappe.get_single("Social Settings")
    params = {
        "response_type": "code",
        "client_id": settings.twitter_client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": "tweet.read tweet.write",
        "state": "twitter",
        "code_challenge": "challenge",  # Added PKCE support
        "code_challenge_method": "plain"
    }
    return f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
@frappe.whitelist(allow_guest=True)
def get_callback_url(platform):
    settings = frappe.get_single("Social Settings")
    return settings.redirect_uri
@frappe.whitelist()
def linkedin_callback(code):
    settings = frappe.get_single("Social Settings")
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_callback_url("linkedin"),
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret
    }
    
    response = requests.post(token_url, data=data)
    tokens = response.json()
    
    platform = frappe.get_doc({
        "doctype": "Social Platform",
        "platform": "LinkedIn",
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token")
    })
    platform.insert()
    
    frappe.msgprint("LinkedIn account connected successfully!")

@frappe.whitelist()
def twitter_callback(code):
    settings = frappe.get_single("Social Settings")
    token_url = "https://api.twitter.com/2/oauth2/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_callback_url("twitter"),
        "client_id": settings.twitter_api_key,
        "client_secret": settings.twitter_api_secret
    }
    
    response = requests.post(token_url, data=data)
    tokens = response.json()
    
    platform = frappe.get_doc({
        "doctype": "Social Platform",
        "platform": "Twitter",
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token")
    })
    platform.insert()
    
    frappe.msgprint("Twitter account connected successfully!")

@frappe.whitelist(allow_guest=True)
def verify_linkedin_connection():
    platforms = frappe.get_all(
        "Social Platform",
        filters={"platform": "LinkedIn"},
        fields=["name", "access_token"]
    )
    
    if not platforms:
        return {"connected": False}
        
    # Test the connection
    try:
        headers = {
            "Authorization": f"Bearer {platforms[0].access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.linkedin.com/v2/me",
            headers=headers
        )
        response.raise_for_status()
        return {"connected": True}
    except:
        return {"connected": False}

@frappe.whitelist(allow_guest=True)
def verify_twitter_connection():
    platforms = frappe.get_all(
        "Social Platform",
        filters={"platform": "Twitter"},
        fields=["name", "access_token"]
    )
    
    if not platforms:
        return {"connected": False}
        
    # Test the connection
    try:
        headers = {
            "Authorization": f"Bearer {platforms[0].access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.twitter.com/2/users/me",
            headers=headers
        )
        response.raise_for_status()
        return {"connected": True}
    except:
        return {"connected": False}