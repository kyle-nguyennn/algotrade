import pandas as pd
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import typing

class Reporter:
    def __init__(self):
        pass
    def send(self, data):
        raise NotImplementedError

class EmailReporter(Reporter):
    def __init__(self, sender: str, receivers: typing.List[str]):
        super().__init__()
        self.sender, self.receivers = sender, receivers

    def send(self, data: pd.DataFrame):
        recipients = self.receivers
        emaillist = [elem.strip().split(',') for elem in recipients]
        msg = MIMEMultipart()
        msg['Subject'] = "Test Report"
        msg['From'] = self.sender

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

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.sendmail(msg['From'], emaillist, msg.as_string())