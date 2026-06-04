import imaplib
import email
from email.header import decode_header
import os
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load env variables for initial setup check (though they should be loaded by main script)
load_dotenv()

def get_imap_connection() -> imaplib.IMAP4_SSL:
    """Establishes and returns an IMAP connection."""
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
    email_acc = os.getenv("EMAIL_ACCOUNT")
    password = os.getenv("EMAIL_APP_PASSWORD")

    if not email_acc or not password:
        raise ValueError("Email credentials not found in environment variables.")

    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_acc, password)
    return mail

def decode_str(s: str) -> str:
    """Decodes email header strings."""
    if not s:
        return ""
    decoded_list = decode_header(s)
    res = ""
    for decoded_string, charset in decoded_list:
        if isinstance(decoded_string, bytes):
            if charset:
                try:
                    res += decoded_string.decode(charset)
                except LookupError:
                    res += decoded_string.decode('utf-8', errors='ignore')
            else:
                res += decoded_string.decode('utf-8', errors='ignore')
        else:
            res += str(decoded_string)
    return res

def get_email_body_and_attachments(msg) -> Tuple[str, List[Dict]]:
    """Extracts the body text and any PDF attachments from an email message."""
    body = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body += part.get_payload(decode=True).decode()
                except Exception:
                    pass
            elif "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = decode_str(filename)
                    if filename.lower().endswith('.pdf'):
                        attachments.append({
                            "filename": filename,
                            "data": part.get_payload(decode=True)
                        })
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except Exception:
            pass

    return body.strip(), attachments

def fetch_emails() -> List[Dict]:
    """Fetches emails based on configuration (.env settings)."""
    mail = get_imap_connection()
    mail.select("inbox")

    since_date = os.getenv("FETCH_SINCE_DATE")
    
    # Build search query
    if since_date:
        search_query = f'(SINCE "{since_date}")'
    else:
        search_query = 'UNSEEN'

    status, messages = mail.search(None, search_query)
    
    fetched_emails = []

    if status == "OK" and messages[0]:
        message_nums = messages[0].split()
        for num in message_nums:
            res, msg_data = mail.fetch(num, "(RFC822)")
            if res == "OK":
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        message_id = msg.get("Message-ID", "").strip()
                        if not message_id:
                            # Fallback if no Message-ID
                            message_id = f"fallback_{num.decode()}"
                            
                        subject = decode_str(msg.get("Subject", ""))
                        sender = decode_str(msg.get("From", ""))
                        date = decode_str(msg.get("Date", ""))
                        
                        body, attachments = get_email_body_and_attachments(msg)

                        fetched_emails.append({
                            "message_id": message_id,
                            "subject": subject,
                            "sender": sender,
                            "date": date,
                            "body": body,
                            "attachments": attachments
                        })
                        
    mail.close()
    mail.logout()
    return fetched_emails
