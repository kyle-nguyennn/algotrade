from email import encoders
from email.mime.base import MIMEBase

import pandas as pd
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib, ssl, os
import smtplib
import typing

from settings import Setting
import logging

from utils import get_logger

logger = get_logger(__name__, logging.INFO)

class Reporter:
    def __init__(self):
        pass
    def send(self, data):
        raise NotImplementedError

class EmailReporter(Reporter):
    ### TODO: get these info from settings
    ssl_port = 465 # for SSL
    tls_port = 587 # for tls
    smtp_server = "smtp.gmail.com"

    def __init__(self, receivers: typing.List[str]):
        super().__init__()
        self.sender = Setting.get().sender_email
        self.receivers = receivers

    def send(self, data: pd.DataFrame, attachments=[]):
        emaillist = [elem.strip().split(',') for elem in self.receivers]
        msg = MIMEMultipart()
        msg['Subject'] = "Test Report"
        msg['From'] = self.sender
        ### Email format ###
        html = """\
        <html>
          <head></head>
          <body>
            {0}
          </body>
        </html>
        """.format(data.to_html())
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
        ### Attachment ###
        if attachments:
            for path in attachments:
                filename = os.path.split(path)[-1]
                with open(path, "rb") as attachment:
                    # Add file as application/octet-stream
                    # Email client can usually download this automatically as attachment
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                # Encode file in ASCII characters to send by email
                encoders.encode_base64(part)
                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}",
                )
                # Add attachment to message and convert message to string
                msg.attach(part)
        # Create a secure SSL context
        context = ssl.create_default_context()
        setting = Setting.get()
        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.tls_port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(self.sender, setting.sender_email_password)
            # Send email here
            server.sendmail(msg['From'], emaillist, msg.as_string())
            logger.info(f"Successfully send email to {emaillist}.")
        except Exception as e:
            # Print any error messages to stdout
            logger.error(str(e))
        finally:
            server.quit()