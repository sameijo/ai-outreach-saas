"""Email sending service — multi-provider (SendGrid, SES, Mailgun, Resend, SMTP)."""

import json
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseEmailProvider:
    """Base class for email providers."""

    async def send(self, to: str, subject: str, html: str, text: str,
                   from_email: str, from_name: str, reply_to: str = "",
                   tracking_id: str = "", headers: Dict = None) -> Dict:
        raise NotImplementedError


class SendGridProvider(BaseEmailProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send(self, to, subject, html, text, from_email, from_name, reply_to="", tracking_id="", headers=None):
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, From, To, Subject, Content, TrackingSettings, OpenTracking, ClickTracking, HtmlContent

        message = Mail(
            from_email=From(from_email, from_name),
            to_emails=To(to),
            subject=Subject(subject),
        )
        message.content = [HtmlContent(html)]
        if text:
            message.content.insert(0, Content("text/plain", text))

        # Tracking
        message.tracking_settings = TrackingSettings(
            open_tracking=OpenTracking(enable=True),
            click_tracking=ClickTracking(enable=True, enable_text=True),
        )

        if reply_to:
            message.reply_to = reply_to

        if headers:
            for k, v in headers.items():
                message.header = {k: v}

        sg = SendGridAPIClient(self.api_key)
        response = sg.send(message)
        return {
            "success": 200 <= response.status_code < 300,
            "message_id": response.headers.get("X-Message-Id", ""),
            "status_code": response.status_code,
        }


class SESProvider(BaseEmailProvider):
    def __init__(self, region: str, access_key: str, secret_key: str):
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key

    async def send(self, to, subject, html, text, from_email, from_name, reply_to="", tracking_id="", headers=None):
        import boto3

        ses = boto3.client(
            "ses",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

        source = f"{from_name} <{from_email}>" if from_name else from_email

        kwargs = {
            "Source": source,
            "Destination": {"ToAddresses": [to]},
            "Message": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html, "Charset": "UTF-8"},
                    **({"Text": {"Data": text, "Charset": "UTF-8"}} if text else {}),
                },
            },
        }
        if reply_to:
            kwargs["ReplyToAddresses"] = [reply_to]

        response = ses.send_email(**kwargs)
        return {
            "success": True,
            "message_id": response["MessageId"],
            "status_code": 200,
        }


class MailgunProvider(BaseEmailProvider):
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain

    async def send(self, to, subject, html, text, from_email, from_name, reply_to="", tracking_id="", headers=None):
        import httpx

        source = f"{from_name} <{from_email}>" if from_name else from_email

        data = {
            "from": source,
            "to": to,
            "subject": subject,
            "html": html,
        }
        if text:
            data["text"] = text
        if reply_to:
            data["h:Reply-To"] = reply_to

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.mailgun.net/v3/{self.domain}/messages",
                auth=("api", self.api_key),
                data=data,
            )
            result = resp.json()
            return {
                "success": resp.status_code == 200,
                "message_id": result.get("id", ""),
                "status_code": resp.status_code,
            }


class ResendProvider(BaseEmailProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send(self, to, subject, html, text, from_email, from_name, reply_to="", tracking_id="", headers=None):
        import resend

        resend.api_key = self.api_key

        source = f"{from_name} <{from_email}>" if from_name else from_email

        params = {
            "from": source,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if text:
            params["text"] = text
        if reply_to:
            params["reply_to"] = reply_to

        response = resend.Emails.send(params)
        return {
            "success": True,
            "message_id": response.get("id", ""),
            "status_code": 200,
        }


class SMTPProvider(BaseEmailProvider):
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send(self, to, subject, html, text, from_email, from_name, reply_to="", tracking_id="", headers=None):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        msg["To"] = to
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to

        if text:
            msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.sendmail(from_email, to, msg.as_string())

        return {"success": True, "message_id": str(uuid.uuid4()), "status_code": 200}


def get_email_provider(provider: str, config: Dict = None) -> BaseEmailProvider:
    """Factory for email providers."""
    config = config or {}

    if provider == "sendgrid":
        api_key = config.get("api_key") or settings.sendgrid_api_key
        if not api_key:
            raise ValueError("SendGrid API key not configured")
        return SendGridProvider(api_key)

    elif provider == "ses":
        return SESProvider(
            region=config.get("region") or settings.aws_ses_region,
            access_key=config.get("access_key") or settings.aws_ses_access_key,
            secret_key=config.get("secret_key") or settings.aws_ses_secret_key,
        )

    elif provider == "mailgun":
        return MailgunProvider(
            api_key=config.get("api_key") or settings.mailgun_api_key,
            domain=config.get("domain") or settings.mailgun_domain,
        )

    elif provider == "resend":
        api_key = config.get("api_key") or settings.resend_api_key
        if not api_key:
            raise ValueError("Resend API key not configured")
        return ResendProvider(api_key)

    elif provider == "smtp":
        return SMTPProvider(
            host=config.get("smtp_host", ""),
            port=config.get("smtp_port", 587),
            username=config.get("smtp_username", ""),
            password=config.get("smtp_password", ""),
            use_tls=config.get("smtp_use_tls", True),
        )

    else:
        raise ValueError(f"Unknown email provider: {provider}")


def inject_tracking(html: str, tracking_id: str, tracking_domain: str) -> str:
    """Inject open tracking pixel and click tracking into HTML email."""
    # Open tracking pixel (1x1 transparent gif)
    pixel = f'<img src="{tracking_domain}/api/v1/track/open/{tracking_id}" width="1" height="1" style="display:none;" />'
    html = html.replace("</body>", f"{pixel}</body>")
    if "</body>" not in html:
        html += pixel

    # Note: Click tracking would require rewriting all <a> href URLs
    # to go through a redirect endpoint. Simplified here.
    return html
