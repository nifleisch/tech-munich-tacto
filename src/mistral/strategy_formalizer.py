import json
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mistral.agent import agent_call

# exposed function: strategy_formalizer()
# This function is used to create a strategy formalization based on the offer and leverage data.
# It assumes the file runtimedata/offers_and_leverages.csv exists and has the following columns: supplier, offer, leverage
# The function will create a strategy formalization based on the data read in and store it in runtimedata/strategy_formalizer_output.json with the following schema:
# {
#     "strategy": {
#         "title": "A descriptive title of the strategy representing the broader idea of the steps",
#         "steps": [
#             {
#                 "action": "The step of the strategy.",
#                 "leverage": "The leverage of the step."
#             }
#         ]
#     }


strategy_formalizer_agent_id = "ag:f9b7aa04:20250315:strategy-formalizer:8eb009de"

def read_offer_and_leverage_data():
    # mock this for now :D
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

def strategy_formalizer():
    message = "Please read in the offer and leverage data and create a strategy formulization based according to your system prompt and based on the data you read in. Do provide a descriptive title for the entire strategy. Do provide descriptive actions and leverages for each step of the strategy."
    response_format = {
        "type": "object",
        "strategy": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A descriptive title of the strategy representing the broader idea of the steps"
                },
                "steps": {
                    "type": "list",
                    "items": {
                        "type": "string",
                        "description": "The steps of the strategy.",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "The step of the strategy."
                            },
                            "leverage": {
                                "type": "string",
                                "description": "The leverage of the step."
                            }
                        },
                        "additionalProperties": False,
                    }
                }
            },
        },
        "additionalProperties": False,
        "required": ["strategy"]
    }

    res = agent_call(strategy_formalizer_agent_id, message, response_format=response_format, tools=tools, tool_name_to_function=tool_name_to_function)
    res_json = json.loads(res)
    print()
    print('Final response:')
    print(json.dumps(res_json, indent=4))

    #write to file
    with open('runtimedata/strategy_formalizer_output.json', 'w') as f:
        json.dump(res_json, f, indent=4)



if __name__ == '__main__':
    strategy_formalizer()
