from mistralai import Mistral
from getpass import getpass
import pandas as pd

def read_csv_file (path_to_table):
    table = pd.read_csv(path_to_table)
    return table

def historic_data(path_to_table, companies_interest):
    table = read_csv_file(path_to_table)
    filtered_table = table[table['supplier'].isin(companies_interest)]
    return "here is the historic data" + filtered_table.to_string()

def price_labor(path_to_table):
    table = read_csv_file(path_to_table)
    highest_year_row = table.loc[table['year'].idxmax()]
    value_for_highest_year = highest_year_row['change_rate']
    return f"price of labor: {value_for_highest_year} in USD"

def comparison_industry(path_to_table, companies_interest):
    table = read_csv_file(path_to_table)
    table = table[table['supplier'].isin(companies_interest)]
    table = table[table['year'].isin([2025])]
    avg = table['base_price'].mean()
    filtered_df = table[table['supplier'].isin(companies_interest)]
    name_value_dict = dict(zip(filtered_df['supplier'], filtered_df['base_price']))

    return f"this is the avg of the supply for this year accross different companies: {avg}, this is the price of this year for the companies of interest {name_value_dict}"

# VOLUME AND PRICE RANGE ARE INPUTS NOT FROM TABLES


# READ CSV
# GENERATE THE METRICS BASED ON THE CSV
# FEED METRICS TO MODEL
# GET RESPONSE
if __name__ == "__main__":
    path_labor = "dataset/labor.csv"
    path_historic = "dataset/supplier_base_price.csv"

    api_key= "EOpj3gbnl2zUsxtUGVC1E3tlA8o7JI5Z"
    client = Mistral(api_key=api_key)
    companies_interest = ["ShaftPro","DriveMaster"]
    labor_price = price_labor(path_labor)
    result_comparison = comparison_industry(path_historic, companies_interest)
    result_historic = historic_data(path_historic, companies_interest)

    system_prompt = """
    You are an Leverage analyzer.
    Your job is to find leverage oppportunities to negotiate the best possible price with a company
    Ideally you suggest negotiation strategies, should I ask for a cheaper price, should I keep the current price,
    any recommendations you can come with before I contact the supplier

    To answer user questions, you have two tools at your disposal.

    Firstly, you will get the companies that interest us and for which you have to generate suggestions

    Secondly, you will get the price range and the volume
    
    Thirdly, the metric values that we have about the supplies and suppliers of interest. That is historic price data
    of the supply for each company, the price of the labor to generate 1 sample of the supply, the average of the unitary price of the supply 
    as well as the price given by each company 

    Use this information to give the suggestions made at the beginning. 
    
    You will always remain factual, you will not hallucinate, and you will say that you don't know if you don't know.
    You will politely ask the user to shoot another question if the question is not related to the Chinook database.
    """
    chat_history = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": str(companies_interest)
        },
        {
            "role": "user",
            "content": result_historic + labor_price + result_comparison
        }
    ]
    chat_response = client.chat.complete(
        model="mistral-large-latest",
        messages=chat_history,
        temperature=1
    )
    print(chat_response.choices[0].message.content)