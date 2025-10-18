"""
Webhook Management Utilities

Manage webhook endpoints and event delivery.
"""

import requests
import hashlib
import hmac
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manages webhook endpoints and delivery."""
    
    def __init__(self):
        """Initialize webhook manager."""
        self.webhooks = {}
        self.delivery_log = []
    
    def register_webhook(self, name: str, url: str, events: List[str], 
                        secret: str = None) -> str:
        """Register a new webhook endpoint."""
        webhook_id = f"webhook_{len(self.webhooks) + 1}"
        
        self.webhooks[webhook_id] = {
            "name": name,
            "url": url,
            "events": events,
            "secret": secret,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Registered webhook: {name} -> {url}")
        return webhook_id
    
    def trigger_webhook(self, event: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger webhooks for a specific event."""
        results = []
        
        for webhook_id, webhook in self.webhooks.items():
            if not webhook["active"] or event not in webhook["events"]:
                continue
            
            try:
                result = self._deliver_webhook(webhook_id, event, data)
                results.append(result)
            except Exception as e:
                logger.error(f"Webhook delivery failed for {webhook_id}: {e}")
                results.append({
                    "webhook_id": webhook_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def _deliver_webhook(self, webhook_id: str, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver webhook payload to endpoint."""
        webhook = self.webhooks[webhook_id]
        
        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "webhook_id": webhook_id
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Add signature if secret is provided
        if webhook["secret"]:
            signature = self._generate_signature(payload, webhook["secret"])
            headers["X-Webhook-Signature"] = signature
        
        response = requests.post(
            webhook["url"],
            json=payload,
            headers=headers,
            timeout=30
        )
        
        result = {
            "webhook_id": webhook_id,
            "event": event,
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "delivered_at": datetime.now().isoformat()
        }
        
        self.delivery_log.append(result)
        return result
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def get_webhook_status(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific webhook."""
        if webhook_id not in self.webhooks:
            return None
        
        webhook = self.webhooks[webhook_id]
        return {
            "id": webhook_id,
            "name": webhook["name"],
            "url": webhook["url"],
            "events": webhook["events"],
            "active": webhook["active"],
            "created_at": webhook["created_at"]
        }
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks."""
        return [self.get_webhook_status(webhook_id) for webhook_id in self.webhooks]
    
    def deactivate_webhook(self, webhook_id: str) -> bool:
        """Deactivate a webhook."""
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id]["active"] = False
            return True
        return False
