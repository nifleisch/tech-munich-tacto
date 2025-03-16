import numpy as np
import pandas as pd
from datetime import datetime
import pathlib
import os


def simulate_brownian(n, drift, volatility, start=1.0):
    """Simulate a Brownian motion with drift.

    Parameters:
        n (int): number of time steps.
        drift (float): constant drift per time step.
        volatility (float): standard deviation of the noise.
        start (float): starting value.

    Returns:
        numpy.array: simulated price series clamped between 0.5 and 2.
    """
    prices = np.empty(n)
    prices[0] = start
    for i in range(1, n):
        # Update using drift and normally distributed noise
        prices[i] = prices[i - 1] + drift + np.random.normal(0, volatility)
    return prices


if __name__ == "__main__":
    dates = pd.date_range(end=datetime.today(), periods=365)
    n = len(dates)
    volatility = 0.01

    # Set drift values: energy and labor go slightly down, steel goes slightly up.
    drift_energy = -0.0006  # Energy prices drift downward
    drift_labor = -0.0004  # Labor prices drift downward
    drift_steel = +0.000  # Steel prices drift upward

    # Simulate price series for each asset
    energy_prices = simulate_brownian(n, drift_energy, volatility)
    labor_prices = simulate_brownian(n, drift_labor, volatility)
    steel_prices = simulate_brownian(n, drift_steel, volatility)

    # Build DataFrames
    energy_df = pd.DataFrame({"date": dates, "price": energy_prices})
    labor_df = pd.DataFrame({"date": dates, "price": labor_prices})
    steel_df = pd.DataFrame({"date": dates, "price": steel_prices})

    script_dir = pathlib.Path(__file__).parent
    # Write DataFrames to CSV files
    labor_df.to_csv(os.path.join(script_dir, "labor_development.csv"), index=False)
    steel_df.to_csv(os.path.join(script_dir, "steel_development.csv"), index=False)
    energy_df.to_csv(os.path.join(script_dir, "energy_development.csv"), index=False)
