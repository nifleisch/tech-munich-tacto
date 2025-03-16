import pandas as pd


# Read in the CSV files
def get_price_to_cost_change():
    # Read in the CSV files
    df_energy = pd.read_csv("dataset/energy.csv")
    df_labor = pd.read_csv("dataset/labor.csv")
    df_steel = pd.read_csv("dataset/steel.csv")
    df_base_price = pd.read_csv("dataset/supplier_base_price.csv")

    # Ensure all datasets have the same keys for merging
    # Assuming they have a common column like 'supplier' and 'year' for merging
    key_columns = ["year"]  # Change this to the actual common keys
    df_base_price["price_pct_change"] = df_base_price.groupby("supplier")[
        "base_price"
    ].pct_change()
    # Merge cost dataframes on supplier and year
    df_costs = (
        0.2 * (df_energy.set_index(key_columns)["change_rate"] - 1)
        + 0.5 * (df_labor.set_index(key_columns)["change_rate"] - 1)
        + 0.3 * (df_steel.set_index(key_columns)["change_rate"] - 1)
    )

    df = df_base_price.join(df_costs, on=key_columns)

    # df['total_cost'] = df_costs
    df["price_to_cost_change"] = df["price_pct_change"] - df["change_rate"]

    df_sum = df.groupby("supplier", dropna=True)["price_to_cost_change"].sum()
    print(df_sum)
    return df_sum.to_string()


def get_trends():
    """get trend in the different sectors"""
    # Read in the CSV files
    df_energy = pd.read_csv("dataset/energy.csv")
    df_labor = pd.read_csv("dataset/labor.csv")
    df_steel = pd.read_csv("dataset/steel.csv")

    def calculate_trend(df, column="change_rate"):
        df = df.sort_values(by="year").tail(3)
        trend_steepness = df[column].diff().mean()
        return trend_steepness

    trend_energy = calculate_trend(df_energy)
    trend_labor = calculate_trend(df_labor)
    trend_steel = calculate_trend(df_steel)

    return f"energy trends: {trend_energy}, labor trends: {trend_labor}, steel trends: {trend_steel}"


def get_historic_values():
    """get historic quality and volume of the different suppliers"""
    df_data = pd.read_csv("dataset/data.csv")
    df_summary = df_data.groupby("supplier", dropna=True).agg(
        quality=("quality", "mean"), volume=("volume", "mean")
    )
    return (
        "quality"
        + df_summary.quality.to_string()
        + "volume: "
        + df_summary.volume.to_string()
    )


def get_rating_of_last_prices():
    """get rating of the last prices"""
    df_base_price = pd.read_csv("dataset/supplier_base_price.csv")
    supplier_classifications = (
        df_base_price.groupby("supplier")["price_classification"]
        .apply(list)
        .reset_index()
    )
    return supplier_classifications.to_string()


def actual_prices():
    table = pd.read_csv("dataset/supplier_base_price.csv")
    table = table[table["year"].isin([2025])]
    name_value_dict = dict(zip(table["supplier"], table["base_price"]))
    return f"these are the actual prices of all the companies {name_value_dict}"
