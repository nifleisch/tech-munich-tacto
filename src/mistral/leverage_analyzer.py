from mistralai import Mistral
from tools.leverage_tools import actual_prices
from tools.eval_data import *
import json

api_key= "EOpj3gbnl2zUsxtUGVC1E3tlA8o7JI5Z"
agent_id = "ag:c6cd1543:20250315:untitled-agent:7942cf08"
mistral = Mistral(api_key=api_key)

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

with open('agents/leverage_analysis_agent_promt.txt', 'r') as file:
    prompt_file = file.read()

system_prompt = prompt_file

def agent_call(agent_id, context, companies_interest, tools=None, verbose=True, max_iteration=20):
    """Call an agent with a message and process the response.

    Args:
        agent_id (str): the agent id
        message (str): The comapnies of interest to send to the agent.
        response_format (json, optional): The expected json schema of the response. Defaults to None.
        tools (list, optional): See above for a tools list. Defaults to None.
        verbose (bool, optional): Whether to print results. Defaults to True.
        max_iteration (int, optional): Maximum iterations to chat with the agent. Defaults to 10.

    Returns:
        str: the response of the agent. If response_format is provided, it will be in the correct format and can be converted to a json object.
    """
    iteration = 0

    chat_history = [
        {
            "role": "system",
            "content": context
        },
        {
            "role":"user",
            "content": f"our order is: acceptable price range: [60,63], volume: 1000, and our companies of interest are: {companies_interest}. Could you help us with leveraging?"
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


if __name__ == "__main__":

    result = agent_call(agent_id, system_prompt, "ShaftPro, DriveMaster", tools=tools, max_iteration=30)
    print(result)