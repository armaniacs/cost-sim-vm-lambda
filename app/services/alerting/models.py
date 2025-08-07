"""
Alert models and enums.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status values."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channel types."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class AlertRule:
    """Defines an alert rule."""
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., ">=", "<=", "==", "!="
    threshold: float
    severity: AlertSeverity
    evaluation_period: int  # seconds
    notification_channels: List[NotificationChannel]
    escalation_rules: List[Dict[str, Any]]
    tags: Dict[str, str]
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if the rule condition is met."""
        if self.condition == ">=":
            return value >= self.threshold
        elif self.condition == "<=":
            return value <= self.threshold
        elif self.condition == "==":
            return value == self.threshold
        elif self.condition == "!=":
            return value != self.threshold
        elif self.condition == ">":
            return value > self.threshold
        elif self.condition == "<":
            return value < self.threshold
        else:
            return False


@dataclass
class Alert:
    """Represents an alert."""
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: str
    metric_name: str
    metric_value: float
    threshold: float
    condition: str
    tags: Dict[str, str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    suppressed_until: Optional[datetime] = None
    suppressed_by: Optional[str] = None
    escalation_level: int = 0
    notification_count: int = 0
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.acknowledged_by = user
        self.updated_at = datetime.now()
    
    def resolve(self, user: Optional[str] = None) -> None:
        """Resolve the alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolved_by = user
        self.updated_at = datetime.now()
    
    def suppress(self, until: datetime, user: str) -> None:
        """Suppress the alert until a specific time."""
        self.status = AlertStatus.SUPPRESSED
        self.suppressed_until = until
        self.suppressed_by = user
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """Check if the alert is active."""
        return self.status == AlertStatus.ACTIVE
    
    def is_suppressed(self) -> bool:
        """Check if the alert is currently suppressed."""
        if self.status != AlertStatus.SUPPRESSED:
            return False
        
        if self.suppressed_until and datetime.now() >= self.suppressed_until:
            # Suppression period has expired
            self.status = AlertStatus.ACTIVE
            self.suppressed_until = None
            self.suppressed_by = None
            self.updated_at = datetime.now()
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'severity': self.severity.value,
            'status': self.status.value,
            'message': self.message,
            'description': self.description,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold': self.threshold,
            'condition': self.condition,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'suppressed_until': self.suppressed_until.isoformat() if self.suppressed_until else None,
            'suppressed_by': self.suppressed_by,
            'escalation_level': self.escalation_level,
            'notification_count': self.notification_count
        }