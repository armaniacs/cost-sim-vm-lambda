"""
Alert correlation engine for grouping and deduplicating related alerts.
"""

import logging
import re
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .models import Alert, AlertSeverity

logger = logging.getLogger(__name__)


class AlertCorrelationEngine:
    """Engine for correlating and deduplicating alerts."""

    def __init__(self):
        self.correlation_rules = []
        self.alert_groups = defaultdict(list)
        self.lock = threading.Lock()

    def add_correlation_rule(self, rule: Dict[str, Any]):
        """Add a correlation rule."""
        with self.lock:
            self.correlation_rules.append(rule)
            logger.info(f"Added correlation rule: {rule.get('name', 'unnamed')}")

    def correlate_alert(self, alert: Alert) -> Optional[str]:
        """Correlate an alert with existing alerts."""
        with self.lock:
            for rule in self.correlation_rules:
                if self._matches_correlation_rule(alert, rule):
                    group_key = self._generate_group_key(alert, rule)
                    self.alert_groups[group_key].append(alert)
                    logger.debug(f"Alert {alert.id} correlated to group {group_key}")
                    return group_key

        return None

    def get_correlated_alerts(self, group_key: str) -> List[Alert]:
        """Get all alerts in a correlation group."""
        with self.lock:
            return self.alert_groups.get(group_key, [])

    def get_active_groups(self) -> Dict[str, List[Alert]]:
        """Get all active correlation groups."""
        with self.lock:
            # Filter out groups with no active alerts
            active_groups = {}
            for group_key, alerts in self.alert_groups.items():
                active_alerts = [alert for alert in alerts if alert.is_active()]
                if active_alerts:
                    active_groups[group_key] = active_alerts
            return active_groups

    def cleanup_resolved_alerts(self):
        """Remove resolved alerts from correlation groups."""
        with self.lock:
            for group_key in list(self.alert_groups.keys()):
                active_alerts = [
                    alert for alert in self.alert_groups[group_key] if alert.is_active()
                ]
                if active_alerts:
                    self.alert_groups[group_key] = active_alerts
                else:
                    del self.alert_groups[group_key]
                    logger.debug(f"Removed empty correlation group: {group_key}")

    def _matches_correlation_rule(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if alert matches a correlation rule."""
        # Check tags matching
        if "tags" in rule:
            for key, value in rule["tags"].items():
                if alert.tags.get(key) != value:
                    return False

        # Check severity matching
        if "severity" in rule:
            if alert.severity != AlertSeverity(rule["severity"]):
                return False

        # Check name pattern matching
        if "name_pattern" in rule:
            if not re.match(rule["name_pattern"], alert.rule_name):
                return False

        # Check metric name matching
        if "metric_name" in rule:
            if alert.metric_name != rule["metric_name"]:
                return False

        # Check custom conditions
        if "conditions" in rule:
            for condition in rule["conditions"]:
                if not self._evaluate_condition(alert, condition):
                    return False

        return True

    def _evaluate_condition(self, alert: Alert, condition: Dict[str, Any]) -> bool:
        """Evaluate a custom condition against an alert."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not all([field, operator, value]):
            return False

        alert_value = getattr(alert, field, None)
        if alert_value is None:
            return False

        if operator == "eq":
            return alert_value == value
        elif operator == "ne":
            return alert_value != value
        elif operator == "gt":
            return alert_value > value
        elif operator == "gte":
            return alert_value >= value
        elif operator == "lt":
            return alert_value < value
        elif operator == "lte":
            return alert_value <= value
        elif operator == "in":
            return alert_value in value
        elif operator == "regex":
            return bool(re.match(value, str(alert_value)))

        return False

    def _generate_group_key(self, alert: Alert, rule: Dict[str, Any]) -> str:
        """Generate a group key for correlated alerts."""
        key_parts = []

        if "group_by" in rule:
            for field in rule["group_by"]:
                if field == "tags":
                    key_parts.append(str(sorted(alert.tags.items())))
                elif field == "severity":
                    key_parts.append(alert.severity.value)
                elif field == "rule_name":
                    key_parts.append(alert.rule_name)
                elif field == "metric_name":
                    key_parts.append(alert.metric_name)
                elif hasattr(alert, field):
                    key_parts.append(str(getattr(alert, field)))

        # If no group_by specified, use rule name
        if not key_parts:
            key_parts.append(alert.rule_name)

        return ":".join(key_parts)

    def get_correlation_stats(self) -> Dict[str, Any]:
        """Get correlation statistics."""
        with self.lock:
            total_groups = len(self.alert_groups)
            total_alerts = sum(len(alerts) for alerts in self.alert_groups.values())
            active_groups = len(
                [
                    group
                    for group in self.alert_groups.values()
                    if any(alert.is_active() for alert in group)
                ]
            )

            return {
                "total_correlation_groups": total_groups,
                "total_correlated_alerts": total_alerts,
                "active_correlation_groups": active_groups,
                "correlation_rules": len(self.correlation_rules),
            }
