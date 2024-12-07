import frappe
import requests
from urllib.parse import urlencode
import base64
from urllib.parse import urlencode

@frappe.whitelist(allow_guest=True)
def get_callback_url(platform):
    settings = frappe.get_single("Social Settings")
    return settings.redirect_uri

@frappe.whitelist(allow_guest=True)
def get_linkedin_auth_url():
    settings = frappe.get_single("Social Settings")
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": "r_liteprofile w_member_social",
        "state": "linkedin",
    }
    return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

@frappe.whitelist(allow_guest=True)
def get_twitter_auth_url():
    settings = frappe.get_single("Social Settings")
    params = {
        "response_type": "code",
        "client_id": settings.twitter_client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": "tweet.read tweet.write users.read offline.access",
        "state": "twitter",
    }
    return f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"

@frappe.whitelist(allow_guest=True)
def oauth_callback(code=None, state=None):
    if not code:
        frappe.throw("No authorization code received")
        
    if state == "linkedin":
        return linkedin_callback(code)
    elif state == "twitter":
        return twitter_callback(code)
    else:
        frappe.throw("Invalid state parameter")

def linkedin_callback(code):
    try:
        settings = frappe.get_single("Social Settings")
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        
        if response.status_code != 200:
            frappe.log_error(
                f"LinkedIn OAuth Error: {response.text}",
                "LinkedIn OAuth Failed"
            )
            frappe.throw(f"Failed to authenticate with LinkedIn: {response.text}")
            
        tokens = response.json()
        
        # Check if platform exists
        existing_platforms = frappe.get_all(
            "Social Platform",
            filters={"platform": "LinkedIn"},
            fields=["name"]
        )
        
        if existing_platforms:
            platform = frappe.get_doc("Social Platform", existing_platforms[0].name)
            platform.access_token = tokens["access_token"]
            if "refresh_token" in tokens:
                platform.refresh_token = tokens["refresh_token"]
            platform.save()
        else:
            platform = frappe.get_doc({
                "doctype": "Social Platform",
                "platform": "LinkedIn",
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token")
            })
            platform.insert()
        
        frappe.db.commit()
        return "LinkedIn authentication successful!"
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LinkedIn OAuth Callback Error")
        frappe.throw(str(e))

def twitter_callback(code):
    try:
        settings = frappe.get_single("Social Settings")
        token_url = "https://api.twitter.com/2/oauth2/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "client_id": settings.twitter_client_id,
        }
        
        auth_header = base64.b64encode(
            f"{settings.twitter_client_id}:{settings.twitter_client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        
        if response.status_code != 200:
            frappe.log_error(
                f"Twitter OAuth Error: {response.text}",
                "Twitter OAuth Failed"
            )
            frappe.throw(f"Failed to authenticate with Twitter: {response.text}")
            
        tokens = response.json()
        
        existing_platforms = frappe.get_all(
            "Social Platform",
            filters={"platform": "Twitter"},
            fields=["name"]
        )
        
        if existing_platforms:
            platform = frappe.get_doc("Social Platform", existing_platforms[0].name)
            platform.access_token = tokens["access_token"]
            if "refresh_token" in tokens:
                platform.refresh_token = tokens["refresh_token"]
            platform.save()
        else:
            platform = frappe.get_doc({
                "doctype": "Social Platform",
                "platform": "Twitter",
                "access_token": tokens["access_token"],
                "refresh_token": tokens.get("refresh_token")
            })
            platform.insert()
        
        frappe.db.commit()
        return "Twitter authentication successful!"
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Twitter OAuth Callback Error")
        frappe.throw(str(e))

@frappe.whitelist()
def verify_connection(platform):
    try:
        platforms = frappe.get_all(
            "Social Platform",
            filters={"platform": platform},
            fields=["access_token"]
        )
        
        if not platforms:
            return {
                "connected": False,
                "message": f"No {platform} connection found"
            }
            
        headers = {
            "Authorization": f"Bearer {platforms[0].access_token}"
        }
        
        if platform == "LinkedIn":
            response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            )
        else:  # Twitter
            response = requests.get(
                "https://api.twitter.com/2/users/me",
                headers=headers
            )
        
        if response.status_code == 200:
            return {
                "connected": True,
                "message": f"Successfully connected to {platform}"
            }
        else:
            return {
                "connected": False,
                "message": f"Invalid or expired {platform} connection"
            }
            
    except Exception as e:
        return {
            "connected": False,
            "message": str(e)
        }