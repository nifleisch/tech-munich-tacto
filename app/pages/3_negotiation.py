import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_extras.switch_page_button import switch_page
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.mistral.leverage_analyzer import leverage_analyzer
from src.mistral.strategy_formalizer import strategy_formalizer
from src.utils import COMPONENT, CUSTOMER
from src.mistral.email_writer import (
    customer_email_agent,
    supplier_email_agent,
    email_thread_to_summary,
)
from elevenlab_api import give_context_and_call

st.set_page_config(
    page_title="Negotiation Agent",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Display header
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.image("app/assets/negotiation_agent.png", use_container_width=True)

st.write("")

# Load data first
# Load offer and leverage data
offer_df = pd.read_csv("runtimedata/offers_and_leverages.csv")

# If leverage column doesn't exist, add it with empty strings
if "leverage" not in offer_df.columns:
    offer_df["leverage"] = ""
    # Save the updated dataframe
    offer_df.to_csv("runtimedata/offers_and_leverages.csv", index=False)

# Convert offer to numeric, forcing errors to NaN
offer_df["offer"] = pd.to_numeric(offer_df["offer"], errors="coerce")

# Load supplier data for quality and reliability
supplier_df = pd.read_csv("dataset/supplier.csv")

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

# Initialize negotiation history in session state if it doesn't exist
if "negotiation_history" not in st.session_state:
    st.session_state["negotiation_history"] = {}
    # Initialize with current offers
    for _, row in offer_df.iterrows():
        supplier = row["supplier"]
        if pd.notna(row["offer"]):
            st.session_state["negotiation_history"][supplier] = [float(row["offer"])]

# Display info banner
st.info(
    f"I've received offers from {len(merged_df)} suppliers for {COMPONENT}. "
    f"Review each offer and decide whether to accept or negotiate.",
    icon="📨",
)

# Check if strategy file exists and display it
strategy_file = "runtimedata/strategy_formalizer_output.json"
if os.path.exists(strategy_file):
    try:
        with open(strategy_file, "r") as f:
            strategy_data = json.loads(f.read())

        if "strategy" in strategy_data:
            strategy = strategy_data["strategy"]

            # Custom CSS for the strategy section
            st.markdown(
                """
            <style>
            .strategy-header {
                background-color: #e6f3e6;
                padding: 10px 15px;
                border-radius: 5px;
                border-left: 5px solid #2e7d32;
                margin-bottom: 15px;
            }
            .strategy-step {
                background-color: #f5f9f5;
                padding: 10px 15px;
                border-radius: 5px;
                border-left: 3px solid #4CAF50;
                margin-bottom: 10px;
            }
            .strategy-title {
                color: #2e7d32;
                font-size: 1.5rem;
                font-weight: bold;
            }
            .strategy-step-title {
                color: #2e7d32;
                font-size: 1.2rem;
                font-weight: bold;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            # Create an expander for the strategy
            with st.expander("📊 Negotiation Strategy", expanded=True):
                # Display each step in the strategy
                for i, step in enumerate(strategy["steps"]):
                    # Step header with custom styling
                    st.markdown(
                        f'<div class="strategy-step"><p class="strategy-step-title">Step {i+1}: {step["action"]}</p>',
                        unsafe_allow_html=True,
                    )

                    # Format the leverage text with bullet points
                    leverage_text = step["leverage"]
                    st.markdown(leverage_text)
                    st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load strategy data: {e}")

# For each supplier, create a section
for _, row in merged_df.iterrows():
    supplier_name = row["supplier"]

    # Create a subheader for each supplier
    st.subheader(f"{supplier_name}")

    # Create two columns for content
    leverage_col, chart_col = st.columns([2, 1])

    with leverage_col:
        # Display the offer and leverage information
        if pd.notna(row["offer"]):
            # Check if we have negotiation history for this supplier
            if supplier_name in st.session_state["negotiation_history"]:
                history = st.session_state["negotiation_history"][supplier_name]

                # Format the offer history with arrows
                offer_history = f"**Offer Price:** {history[0]:.2f}/piece"
                for i in range(1, len(history)):
                    offer_history += f" → {history[i]:.2f}/piece"

                st.markdown(offer_history)
            else:
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

    # Create two columns for buttons, placed below the content
    accept_col, negotiate_col, _ = st.columns([1, 1, 8])

    with accept_col:
        if st.button("Accept Offer", key=f"accept_{supplier_name}"):
            # Store the selected supplier and action in session state
            st.session_state["email_supplier"] = supplier_name
            st.session_state["email_action"] = "accept"
            st.session_state["email_stage"] = "draft"
            st.rerun()

    with negotiate_col:
        if st.button("Negotiate", key=f"negotiate_{supplier_name}"):
            # Store the selected supplier and action in session state
            st.session_state["email_supplier"] = supplier_name
            st.session_state["email_action"] = "negotiate"
            st.session_state["email_stage"] = "draft"
            st.rerun()

    # Check if we need to show the email form for this supplier
    if (
        "email_stage" in st.session_state
        and st.session_state["email_stage"] == "draft"
        and st.session_state["email_supplier"] == supplier_name
    ):
        is_accept = st.session_state["email_action"] == "accept"

        # Check if we already have an email draft in session state
        if "email_draft" not in st.session_state:
            # Generate email draft only if we don't have one yet
            try:
                with st.spinner("Generating email draft..."):
                    email_draft = customer_email_agent(supplier_name, accept=is_accept)
                    # Store the draft in session state
                    st.session_state["email_draft"] = email_draft
            except Exception as e:
                st.error(f"Error generating email: {e}")
                st.session_state.pop("email_stage", None)
                st.rerun()
        else:
            # Use the stored draft
            email_draft = st.session_state["email_draft"]

        # Create a form for the email
        with st.form(key=f"email_form_{supplier_name}"):
            st.markdown(f"**To:** {supplier_name} Procurement Team")
            st.markdown(
                f"**Subject:** {COMPONENT} Order - {'Acceptance' if is_accept else 'Negotiation'}"
            )

            email_text = st.text_area("Email Content", value=email_draft, height=300)

            submitted = st.form_submit_button("Send Email")

        if submitted:
            if not is_accept:
                try:
                    # Get response from supplier
                    with st.spinner("Waiting for supplier response..."):
                        _, new_offer = supplier_email_agent(supplier_name, False)

                    # Update the negotiation history
                    if supplier_name not in st.session_state["negotiation_history"]:
                        st.session_state["negotiation_history"][supplier_name] = [
                            float(row["offer"])
                        ]

                    # Add the new offer to history
                    st.session_state["negotiation_history"][supplier_name].append(
                        float(new_offer)
                    )

                    # Update the offers_and_leverages.csv file
                    offer_df.loc[offer_df["supplier"] == supplier_name, "offer"] = (
                        new_offer
                    )
                    offer_df.to_csv("runtimedata/offers_and_leverages.csv", index=False)

                    st.success(
                        f"Email sent to {supplier_name}! They responded with a new offer of ${new_offer:.2f}/piece"
                    )
                except Exception as e:
                    st.error(f"Error getting supplier response: {e}")
            else:
                st.success(f"Email sent to {supplier_name}!")
                # If this was an acceptance, show balloons
                st.balloons()

            # Clear all email-related session state
            st.session_state.pop("email_stage", None)
            st.session_state.pop("email_supplier", None)
            st.session_state.pop("email_action", None)
            st.session_state.pop("email_draft", None)

            # Rerun to update the UI without the form
            if not is_accept:
                st.rerun()

    # Add a divider between suppliers
    st.markdown("---")

# Add a button to analyze leverage
if st.button("Analyze Leverage Points", type="primary"):
    with st.spinner("Analyzing supplier leverage points..."):
        leverage_analyzer()
        strategy_formalizer()
    st.success("Successfully analyzed supplier leverage points", icon="✅")
    st.rerun()  # Refresh the page to show updated leverage data

# Add this after the "Analyze Leverage Points" button
st.markdown("---")
st.subheader("Supplier Call Simulation")
st.markdown("Simulate a phone call with a supplier using AI voice technology")

call_col1, call_col2 = st.columns([1, 3])

with call_col1:
    supplier_for_call = st.selectbox(
        "Select supplier to call", options=merged_df["supplier"].tolist(), index=0
    )

with call_col2:
    if st.button("Take Call from Supplier", type="primary", key="start_call"):
        try:
            with st.spinner("Preparing call context and connecting..."):
                # Generate a summary of the email thread for context
                summary = email_thread_to_summary(supplier_for_call)

                # Start the call with the context
                give_context_and_call(summary)

            st.success(f"Recieve Call from {supplier_for_call} ...")

        except Exception as e:
            st.error(f"Error initiating call: {e}")
            st.exception(e)
