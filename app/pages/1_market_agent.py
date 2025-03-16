import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import COMPONENT, CUSTOMER
import matplotlib.dates as mdates
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(
    page_title="Market Briefing",
    page_icon=":material/info:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.image("assets/market_briefing.png", use_container_width=True)

st.write("")


def get_latest_purchase(df, customer):
    # Filter by customer
    customer_df = df[df["customer"] == customer]

    # Convert decision_date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(customer_df["decision_date"]):
        customer_df["decision_date"] = pd.to_datetime(customer_df["decision_date"])

    # Sort by date in descending order
    sorted_df = customer_df.sort_values("decision_date", ascending=False)

    # Get the most recent row
    if not sorted_df.empty:
        latest_row = sorted_df.iloc[0]
        return {
            "date": latest_row["decision_date"].strftime("%B %d, %Y"),
            "price": latest_row["price"],
            "supplier": latest_row["supplier"],
            "raw_date": latest_row["decision_date"],  # Add raw date for filtering
        }
    else:
        return None


def create_price_development_plots(latest_purchase):
    """
    Create price development plots based on cost factors and the latest purchase.

    Args:
        latest_purchase: Dictionary containing latest purchase information

    Returns:
        matplotlib figure object
    """
    # Load the development data
    energy_df = pd.read_csv("../dataset/energy_development.csv", parse_dates=["date"])
    labor_df = pd.read_csv("../dataset/labor_development.csv", parse_dates=["date"])
    steel_df = pd.read_csv("../dataset/steel_development.csv", parse_dates=["date"])

    # Function to filter the DataFrame for dates > latest_purchase['date']
    # and normalize by the price at that date (or first available after if missing)
    def filter_and_normalize(df):
        df["date"] = pd.to_datetime(df["date"])
        # Try to get the normalization price at latest_purchase['raw_date']
        norm_series = df.loc[df["date"] == latest_purchase["raw_date"], "price"]
        if norm_series.empty:
            # If exact match is not found, take the first price after latest_purchase date
            norm_value = df.loc[df["date"] > latest_purchase["raw_date"], "price"].iloc[
                0
            ]
        else:
            norm_value = norm_series.iloc[0]
        # Filter for dates greater than latest_purchase['date']
        df_filtered = df[df["date"] > latest_purchase["raw_date"]].copy()
        df_filtered["norm_price"] = df_filtered["price"] / norm_value
        return df_filtered

    # Filter and normalize each asset's data
    energy_filtered = filter_and_normalize(energy_df)
    labor_filtered = filter_and_normalize(labor_df)
    steel_filtered = filter_and_normalize(steel_df)

    # Merge the data on date (assumes that dates are the same across files)
    merged_df = pd.DataFrame({"date": labor_filtered["date"]})
    merged_df["labor"] = labor_filtered["norm_price"].values
    merged_df["steel"] = steel_filtered["norm_price"].values
    merged_df["energy"] = energy_filtered["norm_price"].values

    # Compute weighted composite normalized average
    merged_df["composite"] = (
        0.5 * merged_df["labor"] + 0.3 * merged_df["steel"] + 0.2 * merged_df["energy"]
    )
    # Compute estimated price using the last price from latest_purchase
    merged_df["composite_estimated"] = merged_df["composite"] * latest_purchase["price"]

    # Format dates to show only month and day
    date_format = mdates.DateFormatter("%b %d")  # Format as 'Jan 15'

    # Create the figure with two subplots side by side
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))

    # LEFT PLOT: Normalized development curves
    axs[0].plot(merged_df["date"], merged_df["labor"], color="#4544e4", label="Labor")
    axs[0].plot(merged_df["date"], merged_df["steel"], color="#ab52ba", label="Steel")
    axs[0].plot(merged_df["date"], merged_df["energy"], color="#ffcb7f", label="Energy")
    axs[0].plot(
        merged_df["date"], merged_df["composite"], color="black", label=f"{COMPONENT}"
    )
    axs[0].set_title("Normalized Price of Cost Factors")
    axs[0].legend(frameon=False)
    axs[0].spines["right"].set_visible(False)
    axs[0].spines["top"].set_visible(False)
    axs[0].xaxis.set_major_formatter(date_format)  # Apply the date formatter

    # RIGHT PLOT: Estimated price of the component using cross markers
    axs[1].plot(
        merged_df["date"],
        merged_df["composite_estimated"],
        color="black",
        linestyle="--",
        label=f"{COMPONENT}",
    )
    axs[1].set_title(f"Estimated Price of {COMPONENT} in $/piece")
    axs[1].spines["right"].set_visible(False)
    axs[1].spines["top"].set_visible(False)
    axs[1].xaxis.set_major_formatter(date_format)  # Apply the date formatter

    # Adjust the rotation of date labels for better readability
    for ax in axs:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Adjust layout to accommodate rotated labels
    plt.tight_layout()

    return fig, merged_df


data_df = pd.read_csv("../dataset/data.csv")

# Get the latest purchase information
latest_purchase = get_latest_purchase(data_df, CUSTOMER)

fig_col, _ = st.columns([5, 1])
with fig_col:
    st.info(
        f"Your last purchase of **{COMPONENT}** was on **{latest_purchase['date']}** "
        f"from **{latest_purchase['supplier']}** with an item price of "
        f"**${latest_purchase['price']:.2f}/piece**.",
        icon="💡",
    )

# Display the heading
st.subheader("Price Development")

if latest_purchase:
    st.markdown(
        f"For the component {COMPONENT}, I identified the following **cost factors**:"
    )

    cost_factors = pd.read_csv("../dataset/cost_factors.csv")

    # Define the colors for each segment
    colors = ["#4544e4", "#ab52ba", "#ffcb7f"]

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 0.5))

    # Starting point for the left side of each bar segment
    left = 0

    # Plot each segment as a horizontal bar and add text labels
    for idx, row in cost_factors.iterrows():
        factor_value = row[" factor"]
        label = row["cost_factor"]
        ax.barh(0, factor_value, left=left, color=colors[idx], edgecolor="white")
        # Add the label inside the segment if there's enough space
        # make it bold
        ax.text(
            left + factor_value / 2,
            0,
            f"{factor_value*100:.0f}% {label}",
            va="center",
            ha="center",
            fontsize=8,
            fontweight="bold",
            color="white",
        )
        left += factor_value

    # Remove x and y axis details for a clean look
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)

    # Display the plot in Streamlit
    fig_col, _ = st.columns([5, 1])
    with fig_col:
        st.pyplot(fig)

    st.markdown(
        f"For these cost factors, I observed the following **price changes** since your last purchase on **{latest_purchase['date']}** :"
    )

    # Create and display the price development plots
    try:
        price_fig, merged_df = create_price_development_plots(latest_purchase)
        fig_col, _ = st.columns([5, 1])
        with fig_col:
            st.pyplot(price_fig)

        # Get the latest estimated price
        latest_estimate = merged_df["composite_estimated"].iloc[-1]
        price_change = ((latest_estimate / latest_purchase["price"]) - 1) * 100

        # Display the price change information
        if price_change > 0:
            st.markdown(
                f"Based on these cost factors, the estimated price for **{COMPONENT}** has **increased by {price_change:.1f}%** "
                f"to **${latest_estimate:.2f}/piece** since your last purchase."
            )
        else:
            st.markdown(
                f"Based on these cost factors, the estimated price for **{COMPONENT}** has **decreased by {abs(price_change):.1f}%** "
                f"to **${latest_estimate:.2f}/piece** since your last purchase."
            )

    except Exception as e:
        st.error(f"Error creating price development plots: {e}")

else:
    st.warning(
        f"No purchase history found for {CUSTOMER} for the component {COMPONENT}."
    )


st.subheader("Market Comparison")
fig_col, _ = st.columns([5, 1])
with fig_col:
    st.error(
        f"Based on other deals in the market, I believe that your last purchase price of **${latest_purchase['price']:.2f}/piece** was **too high**.",
        icon="🚨",
    )

# Modified button with navigation functionality
if st.button("Contact Suppliers for new Offers"):
    switch_page("supplier_overview")
