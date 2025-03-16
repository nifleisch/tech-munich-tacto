import json
import pickle
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mistral.agent import agent_call


email_agent_id = "ag:f9b7aa04:20250315:untitled-agent:d38f7f78"

def read_offer_and_leverage_data():
    # mock this for now :D
    df = pd.read_csv('dataset/offers_leverages_mock.csv')
    return df

tool_name_to_function = {
    "read_offer_and_leverage_data": read_offer_and_leverage_data
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_offer_and_leverage_data",
            "description": "This tool reads the offer and leverage data and returns it as a pandas dataframe.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    }
]

def email_agent(supplier_name, accept: bool):

    # Check if there is a previous message thread for this supplier stored in a pickle file
    if os.path.exists(f"email_messages/{supplier_name}_email_chat_history.pkl"):
        with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'rb') as f:
            chat_history = pickle.load(f)
    else:
        chat_history = []

    if len(chat_history) > 0:
        # extend the latest message (which should contain the response email) with the new message
        message = chat_history[-1]['message'] + f'\n\nThe supplier {supplier_name} should be contacted again. The system prompt is: The supplier name you should focus on is {supplier_name}.\n{"You should accept the offer." if accept else "You should do a counteroffer."}\nPlease read in the offer and leverage data.\nWrite an email adhering to the given data and your system prompt.'
        # remove the last message from the chat history, since the response email is now stored in the message
        chat_history = chat_history[:-1]
    else:
        message = f"""The supplier name you should focus on is {supplier_name}.
        {"You should accept the offer." if accept else "You should do a counteroffer."}
        Please read in the offer and leverage data.
        Write an email adhering to the given data and your system prompt."""
    response_format = {
        "email": {
            "type": "string",
        },
        "additionalProperties": False,
        "required": ["email"]
    }

    res, chat_history = agent_call(email_agent_id, message, response_format=response_format, tools=tools, tool_name_to_function=tool_name_to_function, chat_history=chat_history, return_chat_history=True)
    res_json = json.loads(res)

    # Save the chat history to a pickle file
    with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'wb') as f:
        pickle.dump(chat_history, f)

    return res_json

def add_email_response(supplier_name, email):
    # Check if there is a previous message thread for this supplier stored in a pickle file
    if os.path.exists(f"email_messages/{supplier_name}_email_chat_history.pkl"):
        with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'rb') as f:
            chat_history = pickle.load(f)
    else:
        chat_history = []

    chat_history.append({"role": "user", "message": f'Response by the supplier {supplier_name}: ' + email})

    # Save the chat history to a pickle file
    with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'wb') as f:
        pickle.dump(chat_history, f)

    return

if __name__ == '__main__':
    email_drivemaster_1 = email_agent("DriveMaster", accept=False).get('email')
    response_email_1 = """Dear John Dough,

thanks for your reply. I'm sorry, we can not meet your offer.
We are willing to do 980$.

Best regards,
DriveMaster
"""
    add_email_response("DriveMaster", response_email_1)
    email_drivemaster_2 = email_agent("DriveMaster", accept=False).get('email')
    response_email_2 = """Dear John Dough,

thanks for your reply. I'm glad, we can meet your offer.

Best regards,
DriveMaster
    """
    add_email_response("DriveMaster", response_email_2)
    email_drivemaster_3 = email_agent("DriveMaster", accept=True).get('email')

    print('Email to DriveMaster 1:')
    print(email_drivemaster_1)
    print('Response from DriveMaster:')
    print(response_email_1)
    print('Email to DriveMaster 2:')
    print(email_drivemaster_2)
    print('Response from DriveMaster:')
    print(response_email_2)
    print('Email to DriveMaster 3:')
    print(email_drivemaster_3)
