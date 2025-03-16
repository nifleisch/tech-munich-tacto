from mistralai import Mistral
from tools.eval_data import *
import pandas as pd
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

api_key= os.getenv("MISTRAL_API_KEY")
mistral = Mistral(api_key=api_key)

# Exposed function: leverage_analyzer()
# This function is used to find leverage in the negotiation process with suppliers.
# It assumes the file runtimedata/offers_and_leverages.csv exists and has the following columns: supplier, offer
# The function will add a new column leverage to the file with the leverage found for each supplier.

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_price_to_cost_change",
            "description": """
                           A value for each company, the substraction of increased product price over the last 3 years and increased
                           product cost over the last 3 years, indicating if the product has become more expensive.
                           This should indicate a possible leverage (if value is high, the supplier has increased their margin)
                           """,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trends",
            "description": """
                            Values that indicate the trend in each cost sector, giving an indication wether
                            supplier cost should increase or decrease. Can also be used as argument for leverage
                            (example: sector costs have decreased in the last years and product price has increased
                            could give leverage to question current product price)
                            """,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_historic_values",
            "description": """
                           Get historic values of average quality of delivery.
                           If low/lower than other companies this could be a leverage point to negotiate lower prices.
                           This function also gets the volume of average delivery of each supplier.
                           If volume of current order is bigger by a certain amount, this could be used to negotiatefor lower prices.
                           If current volume is lower, this might be used to justify higher prices by the supplier
                           """,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rating_of_last_prices",
            "description": """
                           Get an indication of the last prices of each supplier were industry
                           average, above that or bellow that. Can also be used for leverage.
                           """,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actual_prices",
            "description": """
                           Get actual prices from all the companies.
                           """,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    },
]

tool_name_to_function = {
    "get_rating_of_last_prices": get_rating_of_last_prices,
    "get_price_to_cost_change": get_price_to_cost_change,
    "get_historic_values": get_historic_values,
    "get_trends": get_trends,
    "actual_prices": actual_prices
}


response_format = {
                    "type": "object",
                    "leverages_per_supplier": {
                        "type": "list",
                        "items": {
                            "type": "object",
                            "properties": {
                                "supplier": {
                                    "type": "string"
                                },
                                "leverage": {
                                    "type": "string"
                                }
                            },
                            "required": ["supplier", "leverage"]
                        }
                    },
                    "additionalProperties": False,
                    "required": ["leverages_per_supplier"]
                }

def _agent_call(agent_id, companies_interest, volumes, tools=None, verbose=True, max_iteration=20, response_format=None):
    """Call an agent with a message and process the response.

    Args:
        agent_id (str): the agent id
        context (str): The context to use for the agent to know what if has to do.
        companis_interest (str): list converted to string with the companies of interest
        volumes (str): quantity of supplies to negotiate with each supplier
        tools (list, optional): See above for a tools list. Defaults to None.
        verbose (bool, optional): Whether to print results. Defaults to True.
        max_iteration (int, optional): Maximum iterations to chat with the agent. Defaults to 10.
        response_format (json, optional): The expected json schema of the response. Defaults to None.

    Returns:
        str: the response of the agent. If response_format is provided, it will be in the correct format and can be converted to a json object.
    """
    iteration = 0

    chat_history = [
        {
            "role":"user",
            "content": f"our order is: acceptable price range: [60,63], volumes {volumes}, and our companies of interest are: {companies_interest}. Could you help us with leveraging?"
        }
    ]

    # Main loop to process the request
    while iteration < max_iteration:
        if verbose:
            print(f"Iteration {iteration}")
            print("Chat history:", chat_history)

        res = mistral.agents.complete(messages=chat_history,
                                      agent_id=agent_id,
                                      stream=False,
                                      response_format= None,
                                      tools=tools if tools else None
                                      )
        if verbose:
            print('Agent response:', res.choices[0].message)

        chat_history.append(res.choices[0].message)

        tool_calls = res.choices[0].message.tool_calls

        if not tool_calls:
            print("No more tools used, so the the final response is reached")
            if response_format:
                chat_history.append({
                                    "role":"user",
                                    "content": "could you now please return the suppliers of interest (keys) values should be the leverage arguments and conclusions in markdown format"
                                    })
                res = mistral.agents.complete(messages=chat_history,
                        agent_id=agent_id,
                        stream=False,
                        # response format is only allowed if no tools are provided
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "response",
                                "schema": response_format
                            },
                        }
                    )
            return res.choices[0].message.content


        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_params = json.loads(tool_call.function.arguments)

            function_result = tool_name_to_function[function_name](**function_params)
            function_result = str(function_result)

            chat_history.append({"role": "tool", "name": function_name, "content": function_result, "tool_call_id": tool_call.id})
            if verbose:
                print(f"Tool {function_name} was called with the parameters: {function_params} and the result was: {function_result}")

        iteration += 1


def leverage_analyzer():
    agent_id = os.environ.get("LEVERAGE_ANALYZER_AGENT_ID")

    info_file = pd.read_csv("runtimedata/offers_and_leverages.csv")

    column_values = info_file["supplier"].tolist()

    offer_values = info_file["offer"].tolist()

    result = _agent_call(agent_id, str(column_values), str(offer_values),
                        tools=tools, max_iteration=30, response_format=response_format, verbose=False)

    j_result = json.loads(result)

    info_file["leverage"] = None

    for dct in j_result["leverages_per_supplier"]:
        info_file.loc[info_file['supplier'] == dct["supplier"], "leverage"] = dct["leverage"]

    info_file.to_csv('runtimedata/offers_and_leverages.csv', index=False)



if __name__ == "__main__":
    leverage_analyzer()
