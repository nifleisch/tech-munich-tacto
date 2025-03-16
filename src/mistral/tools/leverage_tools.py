import pandas as pd


def actual_prices():
    table = pd.read_csv("dataset/supplier_base_price.csv")
    table = table[table['year'].isin([2025])]
    name_value_dict = dict(zip(table['supplier'], table['base_price']))

    return f"these are the actual prices of all the companies {name_value_dict}"
