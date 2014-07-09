import os
import sys
import pdb
import smtplib
import email
import email.mime
import email.mime.text
import email.mime.multipart

# You must configure these smpt-server settings before using this script
use_tsl = True # For Gmail use True
smpt_server_requires_authentication = True # For Gmail use True
smtp_username = "mfbfeedback@gmail.com" # This is the smtp server username and also the sender name of the email.
smtp_password = ""
smtp_server_name = 'smtp.gmail.com' # For Gmail use smtp.gmail.com
smtp_server_port = 587 # For Gmail use 587


def sendMail(recipient, title, message, attachment=None):
	# Compile the start of the email message.
	email_message_content = email.mime.multipart.MIMEMultipart()
	email_message_content['From'] = smtp_username
	email_message_content['To'] = recipient
	email_message_content['Subject'] = title

	# Append the user given lines of text to the email message.
	message = '\n\n'.join(message)
	email_message_content.attach(email.mime.text.MIMEText(message.encode('utf-8'), _charset='utf-8'))

	# Read attachment file, encode it and append it to the email message.
	if attachment:
		email_attachment_content = email.mime.base.MIMEBase('application', 'octet-stream')
		email_attachment_content.set_payload(open(attachment, 'rb').read())
		email.encoders.encode_base64(email_attachment_content)
		email_attachment_content.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(attachment))
		email_message_content.attach(email_attachment_content)

	# Email message is ready, before sending it, it must be compiled  into a long string of characters.
	email_message_content_string = email_message_content.as_string()

	# Start communication with the smtp-server.
	try:
		mailServer = smtplib.SMTP(smtp_server_name, smtp_server_port, 'localhost', 10) # Timeout is set to 15 seconds.
		mailServer.ehlo()

		# Check if message size is below the max limit the smpt server announced.
		message_size_is_within_limits = True # Set the default that is used if smtp-server does not annouce max message size.
		if 'size' in mailServer.esmtp_features:
			server_max_message_size = int(mailServer.esmtp_features['size']) # Get smtp server announced max message size
			message_size = len(email_message_content_string) # Get our message size
			if message_size > server_max_message_size: # Message is too large for the smtp server to accept, abort sending.
				message_size_is_within_limits = False
				print('Message_size (', str(message_size), ') is larger than the max supported size (', str(server_max_message_size), ') of server:', smtp_server_name, 'Sending aborted.')
				return False
		if message_size_is_within_limits == True:
			# Uncomment the following line if you want to see printed out the final message that is sent to the smtp server
			if use_tsl:
				mailServer.starttls()
				mailServer.ehlo() # After starting tls, ehlo must be done again.
			if smpt_server_requires_authentication:
				mailServer.login(smtp_username, smtp_password)
			mailServer.sendmail(smtp_username, recipient, email_message_content_string)
		mailServer.close()
		return True

	except smtplib.socket.timeout as reason_for_error:
		print('Error, Timeout error:', reason_for_error)
		return False
	except smtplib.socket.error as reason_for_error:
		print('Error, Socket error:', reason_for_error)
		return False
	except smtplib.SMTPRecipientsRefused as reason_for_error:
		print('Error, All recipients were refused:', reason_for_error)
		return False
	except smtplib.SMTPHeloError as reason_for_error:
		print('Error, The server didn’t reply properly to the HELO greeting:', reason_for_error)
		return False
	except smtplib.SMTPSenderRefused as reason_for_error:
		print('Error, The server didn’t accept the sender address:', reason_for_error)
		return False
	except smtplib.SMTPDataError as reason_for_error:
		print('Error, The server replied with an unexpected error code or The SMTP server refused to accept the message data:', reason_for_error)
		return False
	except smtplib.SMTPException as reason_for_error:
		print('Error, The server does not support the STARTTLS extension or No suitable authentication method was found:', reason_for_error)
		return False
	except smtplib.SMTPAuthenticationError as reason_for_error:
		print('Error, The server didn’t accept the username/password combination:', reason_for_error)
		return False
	except smtplib.SMTPConnectError as reason_for_error:
		print('Error, Error occurred during establishment of a connection with the server:', reason_for_error)
		return False
	except RuntimeError as reason_for_error:
		print('Error, SSL/TLS support is not available to your Python interpreter:', reason_for_error)
		return False

