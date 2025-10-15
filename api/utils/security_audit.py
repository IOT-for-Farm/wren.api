"""
Security Audit and Monitoring for Wren API

This module provides comprehensive security auditing, threat detection,
and security monitoring capabilities.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import ipaddress
import re

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class SecurityEventType(Enum):
    """Types of security events"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALICIOUS_REQUEST = "malicious_request"
    CSRF_ATTACK = "csrf_attack"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    FILE_UPLOAD_ABUSE = "file_upload_abuse"
    API_KEY_ABUSE = "api_key_abuse"
    SESSION_HIJACKING = "session_hijacking"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    request_path: str
    request_method: str
    details: Dict[str, Any]
    source: str = "api"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['threat_level'] = self.threat_level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class SecurityAuditLogger:
    """Security audit logging system"""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.ip_counts: Dict[str, int] = defaultdict(int)
        self.user_counts: Dict[str, int] = defaultdict(int)
    
    def log_event(self, event: SecurityEvent):
        """Log security event"""
        self.events.append(event)
        self.event_counts[event.event_type.value] += 1
        self.ip_counts[event.ip_address] += 1
        
        if event.user_id:
            self.user_counts[event.user_id] += 1
        
        # Log to file
        logger.warning(f"Security Event: {json.dumps(event.to_dict())}")
        
        # Alert on critical events
        if event.threat_level == ThreatLevel.CRITICAL:
            self._send_critical_alert(event)
    
    def _send_critical_alert(self, event: SecurityEvent):
        """Send critical security alert"""
        alert_message = f"""
        CRITICAL SECURITY ALERT
        
        Event Type: {event.event_type.value}
        Threat Level: {event.threat_level.value}
        Timestamp: {event.timestamp.isoformat()}
        IP Address: {event.ip_address}
        User ID: {event.user_id or 'N/A'}
        Request: {event.request_method} {event.request_path}
        Details: {json.dumps(event.details)}
        """
        
        logger.critical(alert_message)
        # Here you would integrate with alerting systems (email, Slack, etc.)
    
    def get_events_by_type(self, event_type: SecurityEventType, limit: int = 100) -> List[SecurityEvent]:
        """Get events by type"""
        return [
            event for event in self.events
            if event.event_type == event_type
        ][-limit:]
    
    def get_events_by_ip(self, ip_address: str, limit: int = 100) -> List[SecurityEvent]:
        """Get events by IP address"""
        return [
            event for event in self.events
            if event.ip_address == ip_address
        ][-limit:]
    
    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[SecurityEvent]:
        """Get events by user ID"""
        return [
            event for event in self.events
            if event.user_id == user_id
        ][-limit:]
    
    def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[SecurityEvent]:
        """Get recent events"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            event for event in self.events
            if event.timestamp >= cutoff_time
        ][-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get security statistics"""
        total_events = len(self.events)
        recent_events = self.get_recent_events(24)
        
        return {
            "total_events": total_events,
            "recent_events_24h": len(recent_events),
            "event_types": dict(self.event_counts),
            "top_ips": dict(sorted(self.ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_users": dict(sorted(self.user_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "threat_levels": self._get_threat_level_stats()
        }
    
    def _get_threat_level_stats(self) -> Dict[str, int]:
        """Get threat level statistics"""
        stats = defaultdict(int)
        for event in self.events:
            stats[event.threat_level.value] += 1
        return dict(stats)


class ThreatDetector:
    """Threat detection and analysis"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'\.\./',
            r'\.\.\\',
            r'null',
            r'%00',
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'sp_',
            r'xp_',
            r'cmd\.exe',
            r'powershell',
            r'bash',
            r'sh\s+',
            r'wget\s+',
            r'curl\s+',
            r'nc\s+',
            r'netcat',
            r'telnet',
            r'ftp\s+',
            r'scp\s+',
            r'rsync\s+'
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def detect_threats(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect potential threats in request data"""
        threats = []
        
        # Check request path
        path_threats = self._check_path(request_data.get('path', ''))
        threats.extend(path_threats)
        
        # Check headers
        header_threats = self._check_headers(request_data.get('headers', {}))
        threats.extend(header_threats)
        
        # Check query parameters
        query_threats = self._check_query_params(request_data.get('query_params', {}))
        threats.extend(query_threats)
        
        # Check request body
        body_threats = self._check_request_body(request_data.get('body', ''))
        threats.extend(body_threats)
        
        return threats
    
    def _check_path(self, path: str) -> List[Dict[str, Any]]:
        """Check request path for threats"""
        threats = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(path):
                threats.append({
                    'type': 'malicious_path',
                    'pattern': self.suspicious_patterns[i],
                    'threat_level': ThreatLevel.HIGH,
                    'description': f'Malicious pattern detected in path: {self.suspicious_patterns[i]}'
                })
        
        return threats
    
    def _check_headers(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check headers for threats"""
        threats = []
        
        for header_name, header_value in headers.items():
            for i, pattern in enumerate(self.compiled_patterns):
                if pattern.search(header_value):
                    threats.append({
                        'type': 'malicious_header',
                        'header': header_name,
                        'pattern': self.suspicious_patterns[i],
                        'threat_level': ThreatLevel.MEDIUM,
                        'description': f'Malicious pattern in header {header_name}: {self.suspicious_patterns[i]}'
                    })
        
        return threats
    
    def _check_query_params(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check query parameters for threats"""
        threats = []
        
        for param_name, param_value in query_params.items():
            param_str = str(param_value)
            for i, pattern in enumerate(self.compiled_patterns):
                if pattern.search(param_str):
                    threats.append({
                        'type': 'malicious_query_param',
                        'parameter': param_name,
                        'pattern': self.suspicious_patterns[i],
                        'threat_level': ThreatLevel.MEDIUM,
                        'description': f'Malicious pattern in query parameter {param_name}: {self.suspicious_patterns[i]}'
                    })
        
        return threats
    
    def _check_request_body(self, body: str) -> List[Dict[str, Any]]:
        """Check request body for threats"""
        threats = []
        
        if not body:
            return threats
        
        body_str = str(body)
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(body_str):
                threats.append({
                    'type': 'malicious_body',
                    'pattern': self.suspicious_patterns[i],
                    'threat_level': ThreatLevel.HIGH,
                    'description': f'Malicious pattern in request body: {self.suspicious_patterns[i]}'
                })
        
        return threats


class IPReputationChecker:
    """IP reputation and geolocation checking"""
    
    def __init__(self):
        self.known_malicious_ips = set()
        self.known_malicious_ranges = []
        self.tor_exit_nodes = set()
        self.vpn_ranges = []
    
    def check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP reputation"""
        result = {
            'ip_address': ip_address,
            'is_malicious': False,
            'is_tor': False,
            'is_vpn': False,
            'is_private': False,
            'country': None,
            'threat_level': ThreatLevel.LOW,
            'reputation_score': 100
        }
        
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            # Check if private IP
            if ip_obj.is_private:
                result['is_private'] = True
                result['reputation_score'] = 90
            
            # Check known malicious IPs
            if ip_address in self.known_malicious_ips:
                result['is_malicious'] = True
                result['threat_level'] = ThreatLevel.CRITICAL
                result['reputation_score'] = 0
            
            # Check malicious IP ranges
            for ip_range in self.known_malicious_ranges:
                if ip_obj in ipaddress.ip_network(ip_range):
                    result['is_malicious'] = True
                    result['threat_level'] = ThreatLevel.HIGH
                    result['reputation_score'] = 10
                    break
            
            # Check Tor exit nodes
            if ip_address in self.tor_exit_nodes:
                result['is_tor'] = True
                result['threat_level'] = ThreatLevel.MEDIUM
                result['reputation_score'] = 30
            
            # Check VPN ranges
            for vpn_range in self.vpn_ranges:
                if ip_obj in ipaddress.ip_network(vpn_range):
                    result['is_vpn'] = True
                    result['threat_level'] = ThreatLevel.MEDIUM
                    result['reputation_score'] = 50
                    break
            
        except ValueError:
            result['threat_level'] = ThreatLevel.HIGH
            result['reputation_score'] = 0
        
        return result
    
    def add_malicious_ip(self, ip_address: str):
        """Add IP to malicious list"""
        self.known_malicious_ips.add(ip_address)
    
    def add_malicious_range(self, ip_range: str):
        """Add IP range to malicious list"""
        self.known_malicious_ranges.append(ip_range)


class SecurityMonitor:
    """Main security monitoring system"""
    
    def __init__(self):
        self.audit_logger = SecurityAuditLogger()
        self.threat_detector = ThreatDetector()
        self.ip_reputation_checker = IPReputationChecker()
        self.anomaly_detector = AnomalyDetector()
    
    def monitor_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor request for security threats"""
        monitoring_result = {
            'threats_detected': [],
            'ip_reputation': {},
            'anomalies': [],
            'recommended_action': 'allow'
        }
        
        # Check IP reputation
        ip_address = request_data.get('ip_address', '')
        if ip_address:
            monitoring_result['ip_reputation'] = self.ip_reputation_checker.check_ip_reputation(ip_address)
        
        # Detect threats
        threats = self.threat_detector.detect_threats(request_data)
        monitoring_result['threats_detected'] = threats
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(request_data)
        monitoring_result['anomalies'] = anomalies
        
        # Determine recommended action
        if threats or anomalies:
            max_threat_level = max(
                [threat.get('threat_level', ThreatLevel.LOW) for threat in threats] +
                [anomaly.get('threat_level', ThreatLevel.LOW) for anomaly in anomalies],
                default=ThreatLevel.LOW
            )
            
            if max_threat_level == ThreatLevel.CRITICAL:
                monitoring_result['recommended_action'] = 'block'
            elif max_threat_level == ThreatLevel.HIGH:
                monitoring_result['recommended_action'] = 'challenge'
            elif max_threat_level == ThreatLevel.MEDIUM:
                monitoring_result['recommended_action'] = 'monitor'
        
        return monitoring_result
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        threat_level: ThreatLevel,
        request_data: Dict[str, Any],
        details: Dict[str, Any]
    ):
        """Log security event"""
        event = SecurityEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            threat_level=threat_level,
            timestamp=datetime.utcnow(),
            user_id=request_data.get('user_id'),
            ip_address=request_data.get('ip_address', ''),
            user_agent=request_data.get('user_agent', ''),
            request_path=request_data.get('path', ''),
            request_method=request_data.get('method', ''),
            details=details
        )
        
        self.audit_logger.log_event(event)
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"sec_{timestamp}_{random_part}"
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard"""
        stats = self.audit_logger.get_statistics()
        recent_events = self.audit_logger.get_recent_events(24, 50)
        
        return {
            'statistics': stats,
            'recent_events': [event.to_dict() for event in recent_events],
            'threat_summary': self._get_threat_summary(),
            'top_threats': self._get_top_threats()
        }
    
    def _get_threat_summary(self) -> Dict[str, int]:
        """Get threat summary"""
        recent_events = self.audit_logger.get_recent_events(24)
        summary = defaultdict(int)
        
        for event in recent_events:
            summary[event.threat_level.value] += 1
        
        return dict(summary)
    
    def _get_top_threats(self) -> List[Dict[str, Any]]:
        """Get top threats"""
        recent_events = self.audit_logger.get_recent_events(24)
        threat_counts = defaultdict(int)
        
        for event in recent_events:
            threat_counts[event.event_type.value] += 1
        
        return [
            {'threat_type': threat_type, 'count': count}
            for threat_type, count in sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]


class AnomalyDetector:
    """Anomaly detection for security monitoring"""
    
    def __init__(self):
        self.normal_patterns = defaultdict(list)
        self.anomaly_thresholds = {
            'requests_per_minute': 100,
            'requests_per_hour': 1000,
            'unique_paths_per_hour': 50,
            'failed_requests_percentage': 50
        }
    
    def detect_anomalies(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in request"""
        anomalies = []
        
        # Check for unusual request patterns
        path_anomaly = self._check_path_anomaly(request_data.get('path', ''))
        if path_anomaly:
            anomalies.append(path_anomaly)
        
        # Check for unusual timing patterns
        timing_anomaly = self._check_timing_anomaly(request_data)
        if timing_anomaly:
            anomalies.append(timing_anomaly)
        
        # Check for unusual user agent patterns
        ua_anomaly = self._check_user_agent_anomaly(request_data.get('user_agent', ''))
        if ua_anomaly:
            anomalies.append(ua_anomaly)
        
        return anomalies
    
    def _check_path_anomaly(self, path: str) -> Optional[Dict[str, Any]]:
        """Check for path anomalies"""
        # Check for unusual path patterns
        if len(path) > 200:
            return {
                'type': 'unusual_path_length',
                'threat_level': ThreatLevel.MEDIUM,
                'description': f'Unusually long path: {len(path)} characters'
            }
        
        # Check for suspicious path patterns
        suspicious_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'null',
            r'%00',
            r'admin',
            r'config',
            r'backup',
            r'test',
            r'debug'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return {
                    'type': 'suspicious_path',
                    'threat_level': ThreatLevel.MEDIUM,
                    'description': f'Suspicious path pattern detected: {pattern}'
                }
        
        return None
    
    def _check_timing_anomaly(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for timing anomalies"""
        # This is a simplified implementation
        # In practice, you'd analyze request timing patterns
        return None
    
    def _check_user_agent_anomaly(self, user_agent: str) -> Optional[Dict[str, Any]]:
        """Check for user agent anomalies"""
        if not user_agent:
            return {
                'type': 'missing_user_agent',
                'threat_level': ThreatLevel.LOW,
                'description': 'Missing user agent header'
            }
        
        # Check for suspicious user agents
        suspicious_agents = [
            'sqlmap',
            'nikto',
            'nmap',
            'masscan',
            'zap',
            'burp',
            'w3af',
            'havij',
            'acunetix',
            'nessus'
        ]
        
        for agent in suspicious_agents:
            if agent.lower() in user_agent.lower():
                return {
                    'type': 'suspicious_user_agent',
                    'threat_level': ThreatLevel.HIGH,
                    'description': f'Suspicious user agent detected: {agent}'
                }
        
        return None


# Global security monitor instance
security_monitor = SecurityMonitor()
