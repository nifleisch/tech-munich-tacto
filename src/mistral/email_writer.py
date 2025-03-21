import json
import pickle
from time import sleep
import pandas as pd
import sys
import os
from mistralai import Mistral
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

api_key = os.getenv("MISTRAL_API_KEY")
mistral = Mistral(api_key=api_key)

from src.mistral.agent import agent_call

# exposed functions: email_agent, supplier_email_agent, delete_email_history
# email_agent: This function is called to generate an email to a supplier based on the supplier name and whether the offer should be accepted or not.
# supplier_email_agent: This function is called to generate a response email from the supplier based on the supplier name and whether the offer should be accepted or not.
# delete_email_history: This function is called to delete the email chat history for a supplier.


email_agent_id = os.environ.get("CUSTOMER_EMAIL_AGENT_ID")
supplier_email_agent_id = os.environ.get("SUPPLIER_EMAIL_AGENT_ID")

def read_offer_and_leverage_data():
    df = pd.read_csv('runtimedata/offers_and_leverages.csv')
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

def customer_email_agent(supplier_name, accept: bool):

    # Check if there is a previous message thread for this supplier stored in a pickle file
    if os.path.exists(f"email_messages/{supplier_name}_email_chat_history.pkl"):
        with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'rb') as f:
            chat_history = pickle.load(f)
    else:
        chat_history = []

    if len(chat_history) > 0:
        message = f'\n\nThe supplier {supplier_name} should be contacted again. The supplier name you should focus on is {supplier_name}.\n{"You should accept the offer." if accept else "You should do a counteroffer."}\nPlease read in the offer and leverage data.\nWrite an email adhering to the given data and your system prompt. The email is an anwser to the previous email.'
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
    directory = "email_messages"
    os.makedirs(directory, exist_ok=True)
    with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'wb') as f:
        pickle.dump(chat_history, f)

    return res_json.get('email')

def supplier_email_agent(supplier_name, accept:bool):
    # Check if there is a previous message thread for this supplier stored in a pickle file
    if os.path.exists(f"email_messages/{supplier_name}_email_chat_history.pkl"):
        with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'rb') as f:
            chat_history = pickle.load(f)
    else:
        raise AssertionError(f"No previous message thread found for supplier {supplier_name}")

    assert len(chat_history) > 0, f"No previous message thread found for supplier {supplier_name}"

    message = f"You got an email from the customer. {'Accept the offer.' if accept else 'Do a counteroffer.'} Base your reply on the email thread given in the chat history. The email is an anwser to the previous email. Do also return the offer amount."

    response_format = {
        "email": {
            "type": "string",
        },
        "offer": {
            "type": "number",
        },
        "additionalProperties": False,
        "required": ["email", "offer"]
    }

    res, chat_history = agent_call(supplier_email_agent_id, message, response_format=response_format, chat_history=chat_history, return_chat_history=True)
    res_json = json.loads(res)
    email = res_json.get('email')
    offer = res_json.get('offer')

    # Save the chat history to a pickle file
    with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'wb') as f:
        pickle.dump(chat_history, f)

    return email, offer

def email_thread_to_summary(supplier_name):
    # make sure the file exists
    if not os.path.exists(f"email_messages/{supplier_name}_email_chat_history.pkl"):
        return "No email chat history found for this supplier."

    with open(f"email_messages/{supplier_name}_email_chat_history.pkl", 'rb') as f:
        chat_history = pickle.load(f)
        chat_history_str = str(chat_history)

        system_prompt = 'You will get a string of the chat_history which is about an email conversation between a customer and a supplier who are negotiating over the price. The supplier wants to maximize the prize while the customer wants to minimize the prize. Please summarize the conversation in a few sentences and in the end emphasize at which price the negotiation is left.'

        res = mistral.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_history_str}
            ],
        )

        return str(res.choices[0].message)

def delete_email_history(supplier_name):
    if os.path.exists(f"email_messages/{supplier_name}_email_chat_history.pkl"):
        os.remove(f"email_messages/{supplier_name}_email_chat_history.pkl")
    return

if __name__ == '__main__':
    email_TorqueTech_1 = customer_email_agent("TorqueTech", accept=False)
    response_email_1, offer_1 = supplier_email_agent("TorqueTech", accept=False)
    email_TorqueTech_2 = customer_email_agent("TorqueTech", accept=True)


    print('Email to TorqueTech 1:')
    print(email_TorqueTech_1)
    print(f'Response from TorqueTech ({offer_1}$):')
    print(response_email_1)
    print('Email to TorqueTech 2:')
    print(email_TorqueTech_2)

    print('Summary:')
    print(email_thread_to_summary("TorqueTech"))


    # write pickled chat history to a txt file as string
    with open('email_messages/TorqueTech_email_chat_history.pkl', 'rb') as f:
        chat_history = pickle.load(f)
    chat_history_str = str(chat_history)
    with open('email_messages/TorqueTech_email_chat_history.txt', 'w') as f:
        f.write(chat_history_str)

    # delete_email_history("TorqueTech")
