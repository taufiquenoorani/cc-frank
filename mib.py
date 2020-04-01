## Taufique Noorani ##
## 12/11/2019 ##
## Frank Bot ##

import os
import time
import json
import threading
import requests
import requests.auth
import logging
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, Comment, CustomField, User
from azure.servicebus.control_client import ServiceBusService
from dotenv import load_dotenv
load_dotenv()

currentBackOff = 0

# Loading Env Variables
FRANK_ZD_CORE_USERNAME = os.getenv('FRANK_ZD_CORE_USERNAME')
FRANK_ZD_CORE_PASSWORD = os.getenv('FRANK_ZD_CORE_PASSWORD')
FRANK_ZD_CORE_SUBDOMAIN = os.getenv('FRANK_ZD_CORE_SUBDOMAIN')
FRANK_AZ_CORE_NAMESPACE = os.getenv('FRANK_AZ_CORE_NAMESPACE')
FRANK_AZ_CORE_KEYNAME = os.getenv('FRANK_AZ_CORE_KEYNAME')
FRANK_AZ_CORE_KEYVALUE = os.getenv('FRANK_AZ_CORE_KEYVALUE')
FRANK_AZ_CORE_ENDPOINT = os.getenv('FRANK_AZ_CORE_ENDPOINT')

# Zendesk Creds
creds = {
    'email': FRANK_ZD_CORE_USERNAME,
    'password': FRANK_ZD_CORE_PASSWORD,
    'subdomain': FRANK_ZD_CORE_SUBDOMAIN
}


bus_service = ServiceBusService(
    service_namespace=FRANK_AZ_CORE_NAMESPACE,
    shared_access_key_name=FRANK_AZ_CORE_KEYNAME,
    shared_access_key_value=FRANK_AZ_CORE_KEYVALUE)

print("Created bus_service object")


def service_bus_listner(callback):
    """thread worker function"""
    global currentBackOff
    print('Started listening to service bus messages')
    maxBackOff = 10
    while True:
        msg = bus_service.receive_queue_message('frank')
        if msg.body is not None:
            process_message(msg)
        else:
            if currentBackOff < maxBackOff:
                currentBackOff += 10

            print("No message to process. Backing off for {0} seconds".format(currentBackOff))
            time.sleep(currentBackOff)


def process_message(msg):
    try:
        message = json.loads(msg.body.decode())
        conversation = message.get("conversation")

        logging.basicConfig(level=logging.INFO, filename='/root/cc-frank/frank.log', filemode='w', format='%(asctime)s :: %(message)s')
        logging.info(message)

        # Setting up conversation ID
        conv = conversation['id']

        try:
            if str(message.get('id')).startswith('f'):
                zd_val = message.get("value")
                teams_name = message.get("from")
                zd_name = teams_name['name']

                # Setting temporay name from Teams
                tmp_name = zd_name.replace(' ', '').split(',')

                # Rearranging name from Teams to send to Zendesk
                full_name = tmp_name[1] + ' ' + tmp_name[0]
                email_add = tmp_name[1].lower() + '.' + tmp_name[0].lower() + '@centurylink.com'

                # Setting variables to create Zendesk ticket
                description, title, impact, history, name, email = zd_val['a4'], zd_val['a2'], zd_val['a7'], zd_val['a8'], full_name, email_add

                create_ticket(title, description, impact, history, name, email)
                send_confirmation(conv)
        except:
            pass

        try:
            # Strip Message
            _msg = message.get('text').strip()
            strip_msg = ""

            if _msg.startswith("<at>Frank</at> "):
                strip_msg = _msg.replace("<at>Frank</at> ", "")
            elif _msg.startswith("<at>Frank</at>"):
                strip_msg = _msg.replace("<at>Frank</at>", "")

            if strip_msg == 'mib' or strip_msg == 'MIB' or strip_msg == 'Mib':
                send_adp(conv)
        except:
            pass

        if (message.get('text') == 'mib') or (message.get('text') == 'MIB') or (message.get('text') == 'make it better') or (message.get('text') == 'Mib'):
            send_adp(conv)

        # print(json.dumps(message, indent=1))

    except Exception as e:
        print(e)
    finally:
        msg.delete()


def create_ticket(title, description, impact, history, name, email):
    global ticket_number

    zendesk_client = Zenpy(**creds)

    # Create a new ticket
    ticket_audit = zendesk_client.tickets.create(Ticket(subject=title, requester=User(name=name, email=email), comment=Comment(
        html_body='<h3>Request Details</h3><pre><code>Title: {}<br>Request: {}<br>'
                  'Impact: {}<br>History: {}</code></pre><h3>Submitter Details</h3><pre><code>'
                  'Name: {}<br>Email: {}</code></pre>'.format(title, description, impact, history, name, email)),
                                         type="problem", priority="normal", requester_id="366101959011",
                                         submitter_id="366101959011", ticket_form_id="360000072631",
                                         group_id="360000964291", collaborator_ids=["443254580", "656182144"], follower_ids=["443254580", "656182144"],
                                         custom_fields=[CustomField(id=360005680151, value='request_to_update_existing_process')]))

    ticket_number = ticket_audit.ticket.id


def send_adp(conv):

    adap_card = json.dumps({
        "type": "message",
        "from": {
            "name": "frank"
        },
        "conversation": {
            "id": conv
        },
        "serviceUrl": "https://smba.trafficmanager.net/amer/",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                            "type": "TextBlock",
                            "spacing": "None",
                            "size": "Large",
                            "weight": "Bolder",
                            "text": "Make It Better"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Please fill out the MIB form and hit Submit. (* is Required)",
                            "isSubtle": True,
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "id": "q2",
                            "separator": True,
                            "text": "Please provide a brief summary of your request (title)*",
                            "wrap": True
                        },
                        {
                            "type": "Input.Text",
                            "id": "a2",
                            "validation": {
                                "necessity": "Required"
                            },
                            "placeholder": "Example: Automated alerts for when a server goes down",
                            "maxLength": "500",
                            "isMultiline": True
                        },
                        {
                            "type": "TextBlock",
                            "id": "q4",
                            "separator": True,
                            "text": "Please give me some more context about your ask (description)*",
                            "wrap": True
                        },
                        {
                            "type": "Input.Text",
                            "id": "a4",
                            "title": "New Input.Toggle",
                            "validation": {
                                "necessity": "Required"
                            },
                            "placeholder": "Example: I would like automation to alert me when a server goes down...",
                            "isMultiline": True
                        },
                        {
                            "type": "TextBlock",
                            "id": "q7",
                            "separator": True,
                            "text": "How often does this happen?",
                            "wrap": True
                        },
                        {
                            "type": "Input.Text",
                            "id": "a7",
                            "title": "",
                            "placeholder": "Example: Daily, Once a week, 5 times a month, ..."
                        },
                        {
                            "type": "TextBlock",
                            "id": "q8",
                            "separator": True,
                            "text": "Are there any other details we need to know in order to properly prioritize your request?",
                            "wrap": True
                        },
                        {
                            "type": "Input.Text",
                            "id": "a8",
                            "title": "",
                            "placeholder": "",
                            "isMultiline": True
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.Submit",
                            "title": "Submit"
                        }
                    ]
                }
            }
        ]
    })

    requests.post(FRANK_AZ_CORE_ENDPOINT, data=adap_card)


def send_confirmation(conv):
    msg = {
        "type": "message",
        "text": "Your request has been submitted successfully. Your ticket number is #<b><a href=https://t3n.zendesk.com/agent/tickets/{}>{}</a></b>".format(ticket_number, ticket_number),
        "from": {
            "name": "frank"
        },
        "conversation": {
            "id": conv
        },
        "serviceUrl": "https://smba.trafficmanager.net/amer/"
    }
    requests.post(FRANK_AZ_CORE_ENDPOINT, json=msg)


if __name__ == '__main__':
    thread = threading.Thread(target=service_bus_listner, args=(process_message,))
    thread.start()

