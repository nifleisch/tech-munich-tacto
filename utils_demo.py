import smtplib
def sendmail_to_user(text,password):
  SERVER = "mail.gmx.net"
  PORT = 587  # Alternativ: 465 für SSL
  EMAIL = r"tacto.supplier@gmx.de"
  PASSWORD = password
  # Verbindung aufbauen
  server = smtplib.SMTP(SERVER, PORT)
  server.ehlo()  
  server.starttls()  # STARTTLS aktivieren
  server.ehlo()

  # Login und E-Mail senden
  server.login(EMAIL, PASSWORD)
  msg = f"""\
  From: tacto.supplier@gmx.de
  To: tacto.user@gmx.de
  Subject: Negotiation

  {text}
  """
  server.sendmail(EMAIL, "tacto.user@gmx.de", msg)
  server.quit()

def sendmail_to_supplier(text,password):
  SERVER = "mail.gmx.net"
  PORT = 587  # Alternativ: 465 für SSL
  EMAIL = r"tacto.user@gmx.de"
  PASSWORD = password
  # Verbindung aufbauen
  server = smtplib.SMTP(SERVER, PORT)
  server.ehlo()  
  server.starttls()  # STARTTLS aktivieren
  server.ehlo()

  # Login und E-Mail senden
  server.login(EMAIL, PASSWORD)
  msg = f"""\
  From: tacto.user@gmx.de
  To: tacto.supplier@gmx.de
  Subject: Negotiation

  {text}
  """
  server.sendmail(EMAIL, "tacto.supplier@gmx.de", msg)
  server.quit()