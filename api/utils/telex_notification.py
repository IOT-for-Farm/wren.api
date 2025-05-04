import requests

class TelexNotification:
    
    def __init__(self, webhook_id: str):
        self.webhook_id = webhook_id
        self.url = f"https://ping.telex.im/v1/webhooks/{self.webhook_id}"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def send_notification(cls, event_name: str, message: str, status: str, username: str='GreenTrac'):
        payload = {
            "event_name": event_name,
            "message": message,
            "status": status,
            "username": username
        }
        
        response = requests.post(
            cls.url,
            json=payload,
            headers=cls.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
