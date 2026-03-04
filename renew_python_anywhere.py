import os
import sys
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv

load_dotenv()


ACCOUNTS = [
    {
        "name": "Slaiz",
        "username": os.environ.get('PA_USERNAME'),
        "password": os.environ.get('PA_PASSWORD'),
        "dashboard_url": "https://www.pythonanywhere.com/user/Slaiz/webapps/"
    },
    {
        "name": "Anker",
        "username": os.environ.get('ANKER_USERNAME'),
        "password": os.environ.get('ANKER_PASSWORD'),
        "dashboard_url": "https://www.pythonanywhere.com/user/ankermax/webapps/"
    },
    {
        "name": "Akel",
        "username": os.environ.get('PA_AKEL_USERNAME'),
        "password": os.environ.get('PA_AKEL_PASSWORD'),
        "dashboard_url": "https://www.pythonanywhere.com/user/akel/webapps/"
    }
]

for acc in ACCOUNTS:
    if not acc["username"] or not acc["password"]:
        print(f"❌ Error: Credentials for {acc['name']} must be set in .env")
        sys.exit(1)

LOGIN_URL = "https://www.pythonanywhere.com/login/"

def renew(username, password, dashboard_url, account_name):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        print(f"🔐 Logging in as {username} ({account_name})...")
        login_page = session.get(LOGIN_URL, timeout=10)
        login_page.raise_for_status()
        
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        
        if not csrf_token:
            print(f"❌ [{account_name}] Could not find CSRF token on login page")
            return False
        
        csrf_token = csrf_token['value']
        
        payload = {
            'csrfmiddlewaretoken': csrf_token,
            'auth-username': username,
            'auth-password': password,
            'login_view-current_step': 'auth'
        }
        
        response = session.post(
            LOGIN_URL, 
            data=payload, 
            headers={'Referer': LOGIN_URL},
            timeout=10,
            allow_redirects=True
        )
        response.raise_for_status()
        
        if "Log out" not in response.text and "logout" not in response.text.lower():
            print(f"❌ [{account_name}] Login failed - 'Log out' not found in response")
            return False
            
        if "login" in response.url.lower():
            print(f"❌ [{account_name}] Login failed - still on login page")
            return False
        
        print(f"✅ [{account_name}] Login successful")
        
        print(f"📊 [{account_name}] Checking dashboard...")
        time.sleep(1) 
        
        dashboard = session.get(dashboard_url, timeout=10)
        dashboard.raise_for_status()
        soup = BeautifulSoup(dashboard.content, 'html.parser')
        
        forms = soup.find_all('form', action=True)
        extend_action = None
        
        for form in forms:
            action = form.get('action', '')
            if "/extend" in action.lower():
                extend_action = action
                print(f"🔍 [{account_name}] Found extend action: {action}")
                break
        
        if not extend_action:
            print(f"ℹ️  [{account_name}] No extend button found. App doesn't need renewal yet.")
            return True
        
        dashboard_csrf = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if not dashboard_csrf:
            print(f"❌ [{account_name}] Could not find CSRF token on dashboard")
            return False
        
        extend_url = f"https://www.pythonanywhere.com{extend_action}"
        print(f"⏰ [{account_name}] Extending web app at {extend_url}...")
        
        result = session.post(
            extend_url,
            data={'csrfmiddlewaretoken': dashboard_csrf['value']},
            headers={'Referer': dashboard_url},
            timeout=10
        )
        result.raise_for_status()
        
        if result.status_code == 200:
            if "webapps" in result.url.lower():
                print(f"✅ [{account_name}] Web app extended successfully!")
                return True
            else:
                print(f"⚠️ [{account_name}] Unexpected redirect to: {result.url}")
                return False
        else:
            print(f"❌ [{account_name}] Extension failed with status: {result.status_code}")
            return False

    except requests.Timeout:
        print(f"❌ [{account_name}] Request timed out")
        return False
    except requests.RequestException as e:
        print(f"❌ [{account_name}] Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ [{account_name}] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    all_success = True
    
    for account in ACCOUNTS:
        print(f"\n{'='*40}\n▶️ Processing account: {account['name']}\n{'='*40}")
        
        success = renew(
            username=account['username'], 
            password=account['password'], 
            dashboard_url=account['dashboard_url'],
            account_name=account['name']
        )
        
        if not success:
            all_success = False
            
        time.sleep(2)
        
    sys.exit(0 if all_success else 1)
