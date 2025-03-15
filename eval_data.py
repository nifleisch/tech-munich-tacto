import pandas as pd

# Read in the CSV files
def get_price_to_cost_change():
    # Read in the CSV files
    df_energy = pd.read_csv('dataset/energy.csv')
    df_labor = pd.read_csv('dataset/labor.csv')
    df_steel = pd.read_csv('dataset/steel.csv')
    df_base_price = pd.read_csv('dataset/supplier_base_price.csv')

    # Ensure all datasets have the same keys for merging
    # Assuming they have a common column like 'supplier' and 'year' for merging
    key_columns = ['year']  # Change this to the actual common keys
    df_base_price['price_pct_change'] = df_base_price.groupby('supplier')['base_price'].pct_change()
    # Merge cost dataframes on supplier and year
    df_costs =  ((df_energy.set_index(key_columns)['change_rate']-1) + \
                (df_labor.set_index(key_columns)['change_rate']-1) + \
                (df_steel.set_index(key_columns)['change_rate']-1)/3)

    df = df_base_price.join(df_costs, on=key_columns)

    #df['total_cost'] = df_costs
    df['price_to_cost_change'] = df['price_pct_change'] - df['change_rate']

    df_sum = df.groupby('supplier', dropna=True)['price_to_cost_change'].sum()
    return df_sum
