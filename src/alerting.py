import logging
import smtplib
import requests
from email.mime.text import MIMEText
from typing import List, Dict

logger = logging.getLogger(__name__)

def send_slack(webhook_url: str, text: str):
    try:
        if not webhook_url or "YOUR_WEBHOOK_HERE" in webhook_url:
            logger.info(f"[ALERT:dry-run] {text}")
            return
        resp = requests.post(webhook_url, json={"text": text}, timeout=10)
        if not (200 <= resp.status_code < 300):
            logger.warning(f"Slack webhook failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"Slack webhook error: {e}")

def send_email(smtp_host: str, smtp_port: int, username: str, password: str, from_addr: str, to_addrs: List[str], subject: str, body: str):
    try:
        if not smtp_host or not username or not password or not to_addrs:
            logger.info(f"[ALERT:dry-run] {subject} -> {to_addrs}: {body}")
            return
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
    except Exception as e:
        logger.warning(f"Email send error: {e}")

def alert(cfg: Dict, subject: str, body: str):
    slack_cfg = cfg.get("alerting", {}).get("slack", {})
    email_cfg = cfg.get("alerting", {}).get("email", {})
    if slack_cfg.get("enabled"):
        send_slack(slack_cfg.get("webhook_url",""), f"*{subject}*\n{body}")
    else:
        logger.info(f"[ALERT] {subject}\n{body}")
    if email_cfg.get("enabled"):
        send_email(
            email_cfg.get("smtp_host",""),
            int(email_cfg.get("smtp_port",587) or 587),
            email_cfg.get("username",""),
            email_cfg.get("password",""),
            email_cfg.get("from_addr",""),
            email_cfg.get("to_addrs",[]),
            subject,
            body,
        )
