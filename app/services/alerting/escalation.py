"""
Alert escalation management.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .models import Alert

logger = logging.getLogger(__name__)


class EscalationManager:
    """Manages alert escalation policies."""

    def __init__(self) -> None:
        self.escalation_policies: Dict[str, Dict[str, Any]] = {}
        self.active_escalations: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def add_escalation_policy(self, policy_id: str, policy: Dict[str, Any]) -> None:
        """Add an escalation policy."""
        required_fields = ["levels"]
        if not all(field in policy for field in required_fields):
            raise ValueError(f"Escalation policy must contain: {required_fields}")

        # Validate levels
        for level in policy["levels"]:
            if "delay_minutes" not in level:
                raise ValueError("Each escalation level must have 'delay_minutes'")
            if "actions" not in level:
                level["actions"] = []

        with self.lock:
            self.escalation_policies[policy_id] = policy
            logger.info(f"Added escalation policy: {policy_id}")

    def start_escalation(self, alert: Alert, policy_id: str) -> bool:
        """Start escalation for an alert."""
        with self.lock:
            if policy_id not in self.escalation_policies:
                logger.warning(f"Escalation policy not found: {policy_id}")
                return False

            if alert.id in self.active_escalations:
                logger.debug(f"Escalation already active for alert {alert.id}")
                return False

            policy = self.escalation_policies[policy_id]
            if not policy["levels"]:
                logger.warning(f"No escalation levels defined for policy: {policy_id}")
                return False

            escalation_data = {
                "alert": alert,
                "policy": policy,
                "policy_id": policy_id,
                "current_level": 0,
                "started_at": datetime.now(),
                "next_escalation_at": datetime.now()
                + timedelta(minutes=policy["levels"][0]["delay_minutes"]),
            }

            self.active_escalations[alert.id] = escalation_data
            logger.info(
                f"Started escalation for alert {alert.id} with policy {policy_id}"
            )
            return True

    def check_escalations(self) -> List[Dict[str, Any]]:
        """Check for alerts that need escalation."""
        escalations_to_process = []

        with self.lock:
            current_time = datetime.now()

            for alert_id, escalation_data in list(self.active_escalations.items()):
                # Skip if alert is no longer active
                if not escalation_data["alert"].is_active():
                    logger.debug(f"Stopping escalation for inactive alert {alert_id}")
                    del self.active_escalations[alert_id]
                    continue

                # Check if escalation is due
                if current_time >= escalation_data["next_escalation_at"]:
                    escalations_to_process.append(escalation_data.copy())

        return escalations_to_process

    def process_escalation(self, escalation_data: Dict[str, Any]) -> bool:
        """Process an escalation step."""
        alert = escalation_data["alert"]
        policy = escalation_data["policy"]
        current_level = escalation_data["current_level"]

        if current_level >= len(policy["levels"]):
            logger.warning(
                f"Escalation level {current_level} exceeds available levels "
                f"for alert {alert.id}"
            )
            return False

        level_config = policy["levels"][current_level]
        logger.info(f"Processing escalation level {current_level} for alert {alert.id}")

        # Update alert escalation level
        alert.escalation_level = current_level + 1

        # Process escalation actions
        success = True
        for action in level_config.get("actions", []):
            try:
                if action["type"] == "notify":
                    success &= self._handle_notify_action(alert, action)
                elif action["type"] == "create_ticket":
                    success &= self._handle_create_ticket_action(alert, action)
                elif action["type"] == "page":
                    success &= self._handle_page_action(alert, action)
                elif action["type"] == "webhook":
                    success &= self._handle_webhook_action(alert, action)
                else:
                    logger.warning(f"Unknown escalation action type: {action['type']}")
            except Exception as e:
                logger.error(
                    f"Error processing escalation action {action['type']}: {e}"
                )
                success = False

        # Schedule next escalation or complete current one
        with self.lock:
            if alert.id in self.active_escalations:
                self.active_escalations[alert.id]["current_level"] += 1

                # Check if there are more levels
                next_level = self.active_escalations[alert.id]["current_level"]
                if next_level < len(policy["levels"]):
                    next_level_config = policy["levels"][next_level]
                    self.active_escalations[alert.id][
                        "next_escalation_at"
                    ] = datetime.now() + timedelta(
                        minutes=next_level_config["delay_minutes"]
                    )
                    logger.debug(
                        f"Scheduled next escalation for alert {alert.id} "
                        f"at level {next_level}"
                    )
                else:
                    logger.info(f"Escalation completed for alert {alert.id}")

        return success

    def stop_escalation(self, alert_id: str) -> bool:
        """Stop escalation for an alert."""
        with self.lock:
            if alert_id in self.active_escalations:
                del self.active_escalations[alert_id]
                logger.info(f"Stopped escalation for alert {alert_id}")
                return True
            return False

    def get_active_escalations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active escalations."""
        with self.lock:
            return {
                alert_id: {
                    "alert_id": alert_id,
                    "policy_id": data["policy_id"],
                    "current_level": data["current_level"],
                    "started_at": data["started_at"].isoformat(),
                    "next_escalation_at": data["next_escalation_at"].isoformat(),
                }
                for alert_id, data in self.active_escalations.items()
            }

    def get_escalation_policies(self) -> Dict[str, Dict[str, Any]]:
        """Get all escalation policies."""
        with self.lock:
            return self.escalation_policies.copy()

    def _handle_notify_action(self, alert: Alert, action: Dict[str, Any]) -> bool:
        """Handle notify escalation action."""
        # This would typically integrate with notification handlers
        recipients = action.get("recipients", [])
        channels = action.get("channels", [])

        logger.info(
            f"Escalation notify action for alert {alert.id}: "
            f"recipients={recipients}, channels={channels}"
        )
        # Implementation would send notifications to specified recipients/channels
        return True

    def _handle_create_ticket_action(
        self, alert: Alert, action: Dict[str, Any]
    ) -> bool:
        """Handle create ticket escalation action."""
        system = action.get("system", "default")
        priority = action.get("priority", "normal")

        logger.info(
            f"Escalation create ticket action for alert {alert.id}: "
            f"system={system}, priority={priority}"
        )
        # Implementation would create ticket in specified system
        return True

    def _handle_page_action(self, alert: Alert, action: Dict[str, Any]) -> bool:
        """Handle page escalation action."""
        on_call_group = action.get("on_call_group")
        method = action.get("method", "sms")

        logger.info(
            f"Escalation page action for alert {alert.id}: "
            f"group={on_call_group}, method={method}"
        )
        # Implementation would page on-call person
        return True

    def _handle_webhook_action(self, alert: Alert, action: Dict[str, Any]) -> bool:
        """Handle webhook escalation action."""
        url = action.get("url")
        action.get("headers", {})

        logger.info(f"Escalation webhook action for alert {alert.id}: url={url}")
        # Implementation would send webhook
        return True

    def cleanup_completed_escalations(self) -> None:
        """Clean up completed escalations."""
        with self.lock:
            completed_alerts = []
            for alert_id, escalation_data in self.active_escalations.items():
                alert = escalation_data["alert"]
                if not alert.is_active() or escalation_data["current_level"] >= len(
                    escalation_data["policy"]["levels"]
                ):
                    completed_alerts.append(alert_id)

            for alert_id in completed_alerts:
                del self.active_escalations[alert_id]
                logger.debug(f"Cleaned up completed escalation for alert {alert_id}")

    def get_escalation_stats(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        with self.lock:
            return {
                "active_escalations": len(self.active_escalations),
                "escalation_policies": len(self.escalation_policies),
                "escalations_by_level": self._get_escalations_by_level(),
            }

    def _get_escalations_by_level(self) -> Dict[int, int]:
        """Get count of escalations by level."""
        level_counts: Dict[int, int] = {}
        for escalation_data in self.active_escalations.values():
            level = escalation_data["current_level"]
            level_counts[level] = level_counts.get(level, 0) + 1
        return level_counts
