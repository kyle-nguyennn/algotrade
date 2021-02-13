import pandas as pd
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
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

    def send(self, data: pd.DataFrame):
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