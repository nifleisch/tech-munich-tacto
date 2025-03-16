import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import COMPONENT, CUSTOMER
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(
    page_title="Negotiation Agent",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Display header
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.image("assets/negotiation_agent.png", use_container_width=True)

st.write("")

# Load data
try:
    # Load offer and leverage data
    offer_df = pd.read_csv("../dataset/offer_and_leverage.csv")

    # Convert offer to numeric, forcing errors to NaN
    offer_df["offer"] = pd.to_numeric(offer_df["offer"], errors="coerce")

    # Load supplier data for quality and reliability
    supplier_df = pd.read_csv("../dataset/supplier.csv")

    # Merge the dataframes
    merged_df = pd.merge(offer_df, supplier_df, on="supplier", how="left")

    # Convert quality and reliability to numeric scores
    quality_map = {"high": 3, "medium": 2, "low": 1}
    reliability_map = {"high": 3, "medium": 2, "low": 1}

    merged_df["quality_score"] = merged_df["quality"].map(quality_map)
    merged_df["reliability_score"] = merged_df["reliability"].map(reliability_map)

    # Convert price to score (3 for lowest, 1 for highest)
    # Only rank non-NaN values
    valid_offers = merged_df["offer"].notna()
    if valid_offers.any():
        price_ranks = merged_df.loc[valid_offers, "offer"].rank(ascending=True)
        merged_df.loc[valid_offers, "price_score"] = 4 - price_ranks
    else:
        merged_df["price_score"] = 2  # Default middle value if no valid offers

    # Display info banner
    st.info(
        f"I've received offers from {len(merged_df)} suppliers for {COMPONENT}. "
        f"Review each offer and decide whether to accept or negotiate.",
        icon="📨",
    )

    # For each supplier, create a section
    for _, row in merged_df.iterrows():
        supplier_name = row["supplier"]

        # Create a subheader for each supplier
        st.subheader(f"{supplier_name}")

        # Create three columns
        offer_col, chart_col, action_col = st.columns([2, 2, 1])

        with offer_col:
            # Display the offer and leverage information
            if pd.notna(row["offer"]):
                st.markdown(f"**Offer Price:** ${row['offer']:.2f}/piece")
            else:
                st.markdown("**Offer Price:** Not specified")

            # Process the leverage text to properly display line breaks and bullet points
            leverage_text = row["leverage"]
            if isinstance(leverage_text, str):
                # Replace dash bullet points with proper markdown bullet points
                leverage_text = leverage_text.replace("- ", "* ")
                # Ensure line breaks are preserved
                leverage_text = leverage_text.replace("\\n", "\n\n")
                st.markdown(leverage_text)
            else:
                st.markdown("No leverage information available.")

        with chart_col:
            # Create radar chart
            fig = go.Figure()

            # Only include price_score if it's valid
            if pd.notna(row["price_score"]):
                r_values = [
                    row["reliability_score"],
                    row["quality_score"],
                    row["price_score"],
                ]
                theta_values = ["Reliability", "Quality", "Price"]
            else:
                r_values = [row["reliability_score"], row["quality_score"]]
                theta_values = ["Reliability", "Quality"]

            fig.add_trace(
                go.Scatterpolar(
                    r=r_values,
                    theta=theta_values,
                    fill="toself",
                    name=supplier_name,
                    line_color="#4544e4",
                )
            )

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 3])),
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=250,
            )

            st.plotly_chart(fig, use_container_width=True)

        with action_col:
            # Add buttons for accept and negotiate
            if st.button("Accept Offer", key=f"accept_{supplier_name}"):
                st.balloons()
                st.success(
                    f"Offer from {supplier_name} accepted! A confirmation has been sent."
                )

            if st.button("Negotiate", key=f"negotiate_{supplier_name}"):
                # Store the selected supplier in session state
                st.session_state["negotiating_supplier"] = supplier_name
                st.session_state["negotiation_stage"] = "counter_offer"
                st.rerun()

        # Add a divider between suppliers
        st.markdown("---")

    # Check if we're in negotiation mode
    if (
        "negotiation_stage" in st.session_state
        and st.session_state["negotiation_stage"] == "counter_offer"
    ):
        supplier = st.session_state["negotiating_supplier"]
        supplier_data = merged_df[merged_df["supplier"] == supplier].iloc[0]

        st.subheader(f"Negotiate with {supplier}")

        with st.form(key="counter_offer_form"):
            current_price = supplier_data["offer"]

            if pd.notna(current_price):
                st.markdown(
                    f"Current offer from {supplier}: **${current_price:.2f}/piece**"
                )

                counter_offer = st.number_input(
                    "Your counter offer ($/piece)",
                    min_value=float(current_price * 0.7),
                    max_value=float(current_price * 0.99),
                    value=float(current_price * 0.9),
                    step=0.01,
                )
            else:
                st.markdown(f"No specific price offered from {supplier}.")
                counter_offer = st.number_input(
                    "Your offer ($/piece)",
                    min_value=50.0,
                    max_value=2000.0,
                    value=500.0,
                    step=0.01,
                )

            message = st.text_area(
                "Message to supplier (optional)",
                value=f"I would like to order {COMPONENT} at ${counter_offer:.2f}/piece.",
            )

            submitted = st.form_submit_button("Send Counter Offer")

        if submitted:
            st.success(
                f"Counter offer of ${counter_offer:.2f}/piece sent to {supplier}!"
            )
            # Reset negotiation state
            st.session_state.pop("negotiation_stage", None)
            st.session_state.pop("negotiating_supplier", None)

except Exception as e:
    st.error(f"Error loading or processing data: {e}")
    st.exception(e)  # This will show the full traceback for debugging
