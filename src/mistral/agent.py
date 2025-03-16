import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mistral.tools.eval_data import get_price_to_cost_change
from mistralai import Mistral

api_key = os.getenv("MISTRAL_API_KEY")
mistral = Mistral(api_key=api_key)

def example_tool(text: str):
    return text[:10]

tools = [
    {
        "type": "function",
        "function": {
            "name": "example_tool",
            "description": "This tool returns the first 10 characters of the provided text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text that needs to be shortened."
                    }
                },
                "required": ["text"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_to_cost_change",
            "description": "This tool calculates the price to cost change per supplier and returns it as a pandas dataframe.",
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
            "name": "read_offer_and_leverage_data",
            "description": "This tool reads the offer and leverage data and returns it as a pandas dataframe.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    }
    #TODO: add new tools here...
]

#TODO: and map their names to the corresponding functions
example_tool_name_to_function = {
    "example_tool": example_tool,
    "get_price_to_cost_change": get_price_to_cost_change
}

example_response_format = {
                    "type": "object",
                    "answer": {
                        "type": "string"
                    },
                    "required": ["answer"]
                }


def agent_call(agent_id, message, response_format=None, tools=None, tool_name_to_function=None, verbose=True, max_iteration=20, chat_history=[], return_chat_history=False):
    """Call an agent with a message and process the response.

    Args:
        agent_id (str): the agent id
        message (str): The message to send to the agent.
        response_format (json, optional): The expected json schema of the response. Defaults to None.
        tools (list, optional): See above for a tools list. Defaults to None.
        tool_name_to_function (dict, optional): A dictionary mapping tool names to the corresponding functions. Defaults to None.
        verbose (bool, optional): Whether to print results. Defaults to True.
        max_iteration (int, optional): Maximum iterations to chat with the agent. Defaults to 10.
        chat_history (list, optional): The chat history in case you had a conversation with this agent before and want to continue it. Defaults to [].
        return_chat_history (bool, optional): Whether to return the chat history. Defaults to False.

    Returns:
        str: the response of the agent. If response_format is provided, it will be in the correct format and can be converted to a json object.
    """
    # assert that the correct tool name to function mapping is provided for the given tools
    if tools:
        # check for each tool that the corresponding function is provided
        for tool in tools:
            assert tool_name_to_function.get(tool["function"]["name"]), f"Please provide the function for the tool {tool['function']['name']}"


    iteration = 0

    chat_history.extend([
        {
            "role": "user",
            "content": message
        }
    ])

    # Main loop to process the request
    while iteration < max_iteration:
        if verbose:
            print(f"Iteration {iteration}")
            print("Chat history:", chat_history)
        res = mistral.agents.complete(messages=chat_history,
            agent_id=agent_id,
            stream=False,
            tools=tools if tools else None
        )
        if verbose:
            print('Agent response:', res.choices[0].message)

        chat_history.append(res.choices[0].message)

        tool_calls = res.choices[0].message.tool_calls

        if not tool_calls:
            print("No more tools used, so the the final response is reached")

            if response_format:
                # we redo the last message with the correct response format, since before we didn't know whther the final response would be reached, i.e. no tools used
                chat_history = chat_history[:-1]
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
                chat_history.append(res.choices[0].message)
                if verbose:
                    print("The final response is being put into the correct format")
            if verbose:
                print('Agent response:', res.choices[0].message)

            if return_chat_history:
                return res.choices[0].message.content, chat_history
            else:
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
    agent_id = "ag:f9b7aa04:20250315:all-purpose-agent:c5338e15"

    # Example 1
    message = "Please shorten the following text down to the first 10 characters and return it to me: 'This is a long text that needs to be shortened.'"
    response_format = {
        "type": "object",
        "answer": {
            "type": "string"
        },
        "required": ["answer"]
    }

    # Example 2
    message = "Please calculate the price to cost change per supplier. And then give the top 2 suppliers with the highest price to cost change and sort them ascendingly."
    response_format = {
        "type": "object",
        "price_change_per_customer": {
            "type": "list",
            "items": {
                "type": "object",
                "properties": {
                    "supplier": {
                        "type": "string"
                    },
                    "price_to_cost_change": {
                        "type": "number"
                    }
                },
                "required": ["supplier", "price_to_cost_change"]
            }
        },
        "additionalProperties": False,
        "required": ["price_per_customer"]
    }

    res = agent_call(agent_id, message, response_format=response_format, tools=tools, tool_name_to_function=example_tool_name_to_function)
    res_json = json.loads(res)
    print()
    print('Final response:')
    print(json.dumps(res_json, indent=4))
