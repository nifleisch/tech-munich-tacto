import streamlit as st
import pandas as pd
from utils import COMPONENT, CUSTOMER
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(
    page_title="Tacto Supplier Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.image("assets/supplier_agent.png", use_container_width=True)

# Load supplier data
try:
    supplier_df = pd.read_csv("../dataset/supplier.csv")
    num_suppliers = len(supplier_df)

    # Display success banner
    st.info(
        f"I found {num_suppliers} suitable suppliers for the component {COMPONENT} for you",
        icon="🔍",
    )

except Exception as e:
    st.error(f"Error loading supplier data: {e}")

st.subheader("Order Details")

st.markdown(f"Please specify the order details for the component {COMPONENT}.")

# Create a form for the order details
with st.form("order_form", enter_to_submit=False):
    # Add input fields for the order details
    order_details = {
        "quantity": st.number_input("Quantity", min_value=1, value=1000),
        "delivery_date": st.date_input("Delivery Date"),
    }
    submitted = st.form_submit_button("Confirm Order Details")

# After the order form and before the "Contact Suppliers" section
if submitted:
    st.success("Order details confirmed! You can now request offers from suppliers.")
else:
    st.info("Please confirm your order details before requesting offers.")

st.subheader("Contact Suppliers")

st.markdown(
    """
1. Review the supplier information below
2. Click "Get Offer" for your preferred suppliers to automatically send an email request via the supplier agent
3. You will usually receive supplier responses via email within 1-2 business days
"""
)

st.write("")

# Load data.csv to get last prices
try:
    data_df = pd.read_csv("../dataset/data.csv")

    # Convert decision_date to datetime for sorting
    data_df["decision_date"] = pd.to_datetime(data_df["decision_date"])

    # Function to get the last price for a specific supplier and customer
    def get_last_price(supplier_name, customer_name):
        # Filter data for the specific supplier and customer
        filtered_df = data_df[
            (data_df["supplier"] == supplier_name)
            & (data_df["customer"] == customer_name)
        ]

        if filtered_df.empty:
            return "No previous orders"

        # Sort by date and get the most recent price
        latest_order = filtered_df.sort_values("decision_date", ascending=False).iloc[0]
        return f"${latest_order['price']:.2f}"

    # Initialize the offer_status in session state if it doesn't exist
    if "offer_status" not in st.session_state:
        st.session_state["offer_status"] = {}

    # Create columns for the supplier information
    col1, col2, col3, col4, col5, _ = st.columns([2, 1, 1, 1, 1, 2])

    # Add column headers
    col1.markdown("**Supplier**")
    col2.markdown("**Quality**")
    col3.markdown("**Reliability**")
    col4.markdown("**Last Price**")
    col5.markdown("**Action**")

    # Display each supplier's information
    for _, supplier in supplier_df.iterrows():
        supplier_name = supplier["supplier"]
        cols = st.columns([2, 1, 1, 1, 1, 2])

        # Supplier name
        cols[0].write(supplier_name)

        # Quality
        cols[1].write(supplier["quality"].capitalize())

        # Reliability
        cols[2].write(supplier["reliability"].capitalize())

        # Last price
        last_price = get_last_price(supplier_name, CUSTOMER)
        cols[3].write(last_price)

        # Check if we've already requested an offer from this supplier
        if supplier_name in st.session_state["offer_status"]:
            # Display "Waiting for offer" instead of the button
            cols[4].markdown("*Waiting for offer...*")
        else:
            # Get Offer button
            if cols[4].button("Get Offer", key=f"offer_{supplier_name}"):
                # Store the selected supplier in session state
                st.session_state["selected_supplier"] = supplier_name
                # Mark this supplier as having a pending offer
                st.session_state["offer_status"][supplier_name] = "pending"
                # Rerun the app to update the UI
                st.rerun()
                # TODO: Add send email

except Exception as e:
    st.error(f"Error loading or processing data: {e}")

# Add the button to go to negotiations
if st.button("Go into Negotiations", type="primary"):
    switch_page("negotiation")
