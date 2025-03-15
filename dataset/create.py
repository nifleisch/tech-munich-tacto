from datetime import datetime, timedelta
import os
import pathlib
import random
from typing import Dict

import pandas as pd
import numpy as np


def set_random_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility"""
    random.seed(seed)
    np.random.seed(seed)


def create_supplier_df() -> pd.DataFrame:
    """
    Creates a DataFrame with 5 suppliers.
    Each supplier has a name, a reliability trait, a quality trait, and a base price (for year 2020).
    The base price is calculated such that "better" traits (high reliability and quality) result in a higher price,
    plus a bit of randomness.
    """
    supplier_names = [
        "DriveMaster",
        "ShaftPro",
        "TorqueTech",
        "SpinWorks",
        "RotorDynamics",
    ]
    reliability_choices = ["low", "medium", "high"]
    quality_choices = ["low", "medium", "high"]
    data = []
    # Map traits to numeric scores for price calculation.
    trait_score = {"low": 0, "medium": 1, "high": 2}

    for name in supplier_names:
        reliability = random.choice(reliability_choices)
        quality = random.choice(quality_choices)
        # Base price starts at $50 and is increased by trait scores (each point adds about $5)
        base = 50 + (trait_score[reliability] + trait_score[quality]) * 5
        # Add some randomness (±$2)
        base_price = base + random.uniform(-2, 2)
        data.append(
            {
                "supplier": name,
                "reliability": reliability,
                "quality": quality,
                "base_price": round(base_price, 2),
            }
        )
    supplier_df = pd.DataFrame(data)
    return supplier_df


def create_steel_df() -> pd.DataFrame:
    """
    Creates a DataFrame for steel price change rates from 2020 to 2025.
    Each year gets a change_rate (for example, 0.85 or 1.20).
    """
    years = list(range(2020, 2026))
    change_rates = [round(random.uniform(0.95, 1.05), 2) for _ in years]
    steel_df = pd.DataFrame({"year": years, "change_rate": change_rates})
    return steel_df

def create_energy_df() -> pd.DataFrame:
    """
    Creates a DataFrame for energy price change rates from 2020 to 2025.
    """
    years = list(range(2020, 2026))
    change_rates = [round(random.uniform(0.95, 1.05), 2) for _ in years]
    energy_df = pd.DataFrame({"year": years, "change_rate": change_rates})
    return energy_df

def create_labor_df() -> pd.DataFrame:
    """
    Creates a DataFrame for labor cost change rates from 2020 to 2025.
    """
    years = list(range(2020, 2026))
    change_rates = [round(random.uniform(0.85, 1.05), 2) for _ in years]
    labor_df = pd.DataFrame({"year": years, "change_rate": change_rates})
    return labor_df


def create_supplier_base_price_df(
    supplier_df: pd.DataFrame, steel_df: pd.DataFrame, labor_df: pd.DataFrame
) -> pd.DataFrame:
    """
    For each supplier, calculates the evolving base price from 2021 to 2025.
    Assumes the supplier's initial base_price is for 2020.
    Each subsequent year's price is computed by applying the steel and labor change factors.
    The weighted effect is modeled using a weighted geometric mean (30% steel, 70% labor).
    """
    years = list(range(2021, 2026))
    records = []
    # Create lookup dictionaries for change rates by year.
    steel_rates = steel_df.set_index("year")["change_rate"].to_dict()
    labor_rates = labor_df.set_index("year")["change_rate"].to_dict()

    for _, row in supplier_df.iterrows():
        supplier = row["supplier"]
        price_prev = row["base_price"]  # price for 2020
        for year in years:
            steel_factor = steel_rates[year]
            labor_factor = labor_rates[year]
            # Weighted geometric mean: exp(0.3*ln(steel) + 0.7*ln(labor))
            multiplier = (steel_factor**0.3) * (labor_factor**0.7)
            price_current = price_prev * multiplier
            if (year in [2021, 2022, 2023] and supplier == "RotorDynamics") or (year in [2021, 2022, 2023] and supplier == "TorqueTech") or (year in [2024,2025] and supplier =="TorqueTech"):
                records.append(
                    {
                        "supplier": supplier,
                        "year": year,
                        "base_price": round(price_current, 2),
                    }
                )
            else:
                records.append(
                    {
                        "supplier": supplier,
                        "year": year,
                        "base_price": np.nan,
                    }
                )
            # Update for cumulative effect in subsequent years.
            price_prev = price_current
    supplier_base_price_df = pd.DataFrame(records)


    # Step 1: Calculate the average industry price by year
    average_industry_price = supplier_base_price_df.groupby('year')['base_price'].mean()

    # Step 2: Sample a random number from uniform(0.95, 1.05) for each year and multiply by the average industry price
    random_factors = np.random.uniform(0.95, 1.05, size=len(average_industry_price))
    adjusted_prices = average_industry_price * random_factors

    # Step 3: Merge adjusted prices back into the supplier_base_price_df
    supplier_base_price_df = supplier_base_price_df.merge(adjusted_prices.rename('adjusted_price'), 
                                                        left_on='year', 
                                                        right_index=True, 
                                                        how='left')

    # Step 4: Create the "high", "avg", "low" classification
    def classify_price(row):
        if row['base_price'] < 1.05 * row['adjusted_price'] and row['base_price'] > 0.95 * row['adjusted_price']:
            return "avg"
        elif row['base_price'] >= 1.05 * row['adjusted_price']:
            return 'high'
        elif row['base_price'] <= 0.95 * row['adjusted_price']:
            return 'low'
        else:
            return 'None'
 
    supplier_base_price_df['price_classification'] = supplier_base_price_df.apply(classify_price, axis=1)

    return supplier_base_price_df


def create_customer_df() -> pd.DataFrame:
    """
    Creates a DataFrame with 10 customers.
    Each customer has a name and a randomly assigned size between 1 and 3.
    """
    customer_names = [
        "Acme Corp",
        "Beta Industries",
        "Gamma Ltd",
        "Delta Enterprises",
        "Epsilon LLC",
        "Zeta Systems",
        "Eta Holdings",
        "Theta Manufacturing",
        "Iota Solutions",
        "Kappa Technologies",
    ]
    data = []
    for name in customer_names:
        size = random.randint(1, 3)
        data.append({"customer": name, "size": size})
    customer_df = pd.DataFrame(data)
    return customer_df


def create_customer_supplier_df(
    customer_df: pd.DataFrame, supplier_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Creates a DataFrame containing every customer–supplier pair.
    For each pair, a 'relationship' value between 1 and 5 is assigned.
    The relationship value is biased such that larger customers (size 2 or 3) tend to have better (higher) values.
    """
    records = []
    for _, cust in customer_df.iterrows():
        for _, supp in supplier_df.iterrows():
            # Use a normal distribution centered at (customer_size + 1)
            rel = int(round(np.random.normal(loc=cust["size"] + 1, scale=1)))
            # Ensure the relationship value is within 1 and 5.
            rel = max(1, min(5, rel))
            records.append(
                {
                    "customer": cust["customer"],
                    "supplier": supp["supplier"],
                    "relationship": rel,
                }
            )
    customer_supplier_df = pd.DataFrame(records)
    return customer_supplier_df


def random_date(start: datetime, end: datetime) -> datetime:
    """
    Returns a random datetime between two datetime objects.
    """
    delta = end - start
    int_delta = delta.days
    random_day = random.randrange(int_delta)
    return start + timedelta(days=random_day)


def create_data_df_with_supplier(
    customer_supplier_df: pd.DataFrame,
    supplier_base_price_df: pd.DataFrame,
    customer_df: pd.DataFrame,
    supplier_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Creates the final events DataFrame (data_df) with 100 rows.
    For each event:
      - A random decision date between 2021 and 2024 is selected.
      - A customer–supplier pair is sampled from customer_supplier_df weighted by the 'relationship' factor.
      - The event volume is sampled based on the customer's size.
      - An arrival delay between 30 and 120 days is randomly chosen.
      - An event-level reliability value is sampled based on the supplier's reliability trait.
      - A quality score is sampled based on the supplier's quality trait.
      - The event price is computed based on the supplier's base price for the event year,
        and is adjusted by volume, arrival delay, and relationship (with added noise).
    """
    records = []
    # Create look-up dictionaries.
    customer_size = customer_df.set_index("customer")["size"].to_dict()
    supplier_traits = supplier_df.set_index("supplier")[
        ["reliability", "quality"]
    ].to_dict(orient="index")

    # For weighted sampling from customer_supplier_df, use relationship as weight.
    cs_df = customer_supplier_df.copy()
    weights = cs_df["relationship"].astype(float)
    probabilities = weights / weights.sum()

    # Define event date range (2021-01-01 to 2024-12-31)
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2024, 12, 31)

    for _ in range(100):
        decision_date = random_date(start_date, end_date)
        event_year = decision_date.year

        # Sample one customer-supplier pair (weighted by relationship)
        cs_row = cs_df.sample(n=1, weights=probabilities).iloc[0]
        customer = cs_row["customer"]
        supplier = cs_row["supplier"]
        relationship = cs_row["relationship"]
        size = customer_size[customer]
        # Volume is based on customer size: larger companies order more.
        volume = random.randint(50 * size, 100 * size)
        # Arrival delay between 30 and 120 days.
        arrival_delay = random.randint(30, 120)

        # Reliability value based on supplier's reliability trait.
        # Mapping: low -> mean 2, medium -> mean 0, high -> mean -2.
        rel_trait = supplier_traits[supplier]["reliability"]
        rel_mean = {"low": 2, "medium": 0, "high": -2}[rel_trait]
        reliability_val = int(
            np.clip(round(np.random.normal(loc=rel_mean, scale=2)), -5, 5)
        )

        # Quality score based on supplier's quality trait.
        qual_trait = supplier_traits[supplier]["quality"]
        if qual_trait == "low":
            quality_val = round(random.uniform(0.90, 0.93), 2)
        elif qual_trait == "medium":
            quality_val = round(random.uniform(0.93, 0.97), 2)
        else:  # high
            quality_val = round(random.uniform(0.97, 1.0), 2)

        # Get the supplier's base price for the event year.
        base_price_record = supplier_base_price_df[
            (supplier_base_price_df["supplier"] == supplier)
            & (supplier_base_price_df["year"] == event_year)
        ]
        if not base_price_record.empty and base_price_record.iloc[0]["base_price"] is not np.nan:
            supplier_base_price = base_price_record.iloc[0]["base_price"]
        else:
            supplier_base_price = np.nan

        # Price calculation:
        # The formula adjusts the base price by discount factors from volume, arrival delay, and relationship.
        # Higher volume, longer arrival, and better relationship (higher number) lead to lower price.
        discount = 0.0005 * volume + 0.001 * arrival_delay + 0.01 * relationship
        # Add a little randomness from a normal noise.
        if supplier_base_price is not np.nan:
            price = supplier_base_price * (1 - discount) + np.random.normal(0, 1)
            price = round(max(price, 0), 2)  # Ensure price is non-negative.
        else:
            price = np.nan

        records.append(
            {
                "decision_date": decision_date.date(),
                "customer": customer,
                "supplier": supplier,
                "relationship": relationship,  # This will be removed later
                "volume": volume,
                "arrival_delay": arrival_delay,
                "reliability": reliability_val,
                "quality": quality_val,
                "price": price,
            }
        )

    # Create DataFrame from records
    data_df = pd.DataFrame(records)

    # Sort by decision_date
    data_df = data_df.sort_values(by="decision_date")

    # Remove the relationship column from the final DataFrame
    data_df = data_df.drop(columns=["relationship"])

    return data_df


def create_mock_datasets() -> Dict[str, pd.DataFrame]:
    """
    Calls all helper functions and returns a dictionary with all DataFrames:
      - supplier
      - steel
      - labor
      - supplier_base_price
      - customer
      - customer_supplier
      - data
    """
    # Set random seeds at the start
    set_random_seeds()

    supplier_df = create_supplier_df()
    steel_df = create_steel_df()
    labor_df = create_labor_df()
    energy_df = create_energy_df()
    supplier_base_price_df = create_supplier_base_price_df(
        supplier_df, steel_df, labor_df
    )
    
    customer_df = create_customer_df()
    customer_supplier_df = create_customer_supplier_df(customer_df, supplier_df)
    data_df = create_data_df_with_supplier(
        customer_supplier_df, supplier_base_price_df, customer_df, supplier_df
    )

    return {
        "supplier": supplier_df,
        "steel": steel_df,
        "labor": labor_df,
        "energy": energy_df,
        "supplier_base_price": supplier_base_price_df,
        "customer": customer_df,
        "customer_supplier": customer_supplier_df,
        "data": data_df,
    }


if __name__ == "__main__":
    # Get the directory where the script is located
    script_dir = pathlib.Path(__file__).parent.absolute()

    # Create datasets
    datasets = create_mock_datasets()

    for name, df in datasets.items():
        file_path = os.path.join(script_dir, f"{name}.csv")
        df.to_csv(file_path, index=False)
        print(f"Saved {name} to {file_path}")
