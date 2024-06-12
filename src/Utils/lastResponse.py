from twilio.rest import Client
import os

def get_last_word(message):
    words = message.split()
    last_word = words[-1] if words else None
    return last_word

def get_last_message_sent_to_user(data):
    
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    
    my_number = data['my_number']
    guest_number = data['guest_number']
    
    client = Client(account_sid, auth_token)

    messages = client.messages.list(
        from_=my_number,
        to=guest_number,
        limit=1
    )
    
    msg_sid = messages[0].sid
    message = client.messages(msg_sid).fetch()
    
    return get_last_word(message.body) if messages else None