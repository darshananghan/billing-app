import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
import certifi

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Billing System", layout="wide")

# ================= DATABASE CONNECTION =================

@st.cache_resource
def get_collection():
    client = MongoClient(
        "mongodb+srv://drshnanghan_db_user:7AxFQ4OPNDfmQVjj@cluster1.nsxghqy.mongodb.net/?appName=Cluster1",
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    db = client["billing_db"]
    collection = db["bills"]
    return collection

collection = get_collection()

# Create unique index only once
@st.cache_resource
def ensure_index():
    collection.create_index("bill_number", unique=True)

ensure_index()

# ================= CALCULATION FUNCTION =================

def calculate_interest(bill_date, bill_amount, due_days, payment_date, monthly_rate):
    due_date = bill_date + timedelta(days=due_days)
    delay_days = (payment_date - due_date).days

    if delay_days < 0:
        delay_days = 0

    daily_rate = monthly_rate / 30
    interest = bill_amount * (daily_rate / 100) * delay_days
    total_amount = bill_amount + interest

    return delay_days, interest, total_amount


# ================= HEADER =================

st.markdown(
    "<h1 style='text-align: center;'>📄 Billing Interest Management System</h1>",
    unsafe_allow_html=True
)

menu = st.radio(
    "",
    ["Interest Calculator", "Store Bill", "View Records"],
    horizontal=True
)

st.markdown("---")

# =========================================================
# 1️⃣ INTEREST CALCULATOR
# =========================================================

if menu == "Interest Calculator":

    st.subheader("🧮 Simple Interest Calculator")

    with st.form("calculator_form"):

        col1, col2 = st.columns(2)

        with col1:
            bill_date = st.date_input("Bill Date")
            bill_amount = st.number_input("Bill Amount", min_value=0.0)
            due_days = st.number_input("Due Days", min_value=0)

        with col2:
            payment_date = st.date_input("Payment Date")
            monthly_rate = st.number_input("Monthly Interest Rate (%)", min_value=0.0)

        calculate_btn = st.form_submit_button("Calculate Interest")

    if calculate_btn:
        delay, interest, total = calculate_interest(
            bill_date, bill_amount, due_days, payment_date, monthly_rate
        )

        st.success(f"Delay Days: {delay}")
        st.success(f"Interest: ₹{interest:.2f}")

# =========================================================
# 2️⃣ STORE BILL
# =========================================================

elif menu == "Store Bill":

    st.subheader("💾 Store Bill in Database")

    with st.form("store_form"):

        col1, col2 = st.columns(2)

        with col1:
            bill_number = st.text_input("Bill Number (Primary Key)")
            party_name = st.text_input("Party Name")
            bill_date = st.date_input("Bill Date")
            bill_amount = st.number_input("Bill Amount", min_value=0.0)
            due_days = st.number_input("Due Days", min_value=0)

        with col2:
            payment_date = st.date_input("Payment Date")
            monthly_rate = st.number_input("Monthly Interest Rate (%)", min_value=0.0)

        save_btn = st.form_submit_button("Calculate & Save")

    if save_btn:

        try:
            delay, interest, total = calculate_interest(
                bill_date, bill_amount, due_days, payment_date, monthly_rate
            )

            data = {
                "bill_number": bill_number,
                "party_name": party_name,
                "bill_date": datetime.combine(bill_date, datetime.min.time()),
                "bill_amount": bill_amount,
                "due_days": due_days,
                "payment_date": datetime.combine(payment_date, datetime.min.time()),
                "monthly_rate": monthly_rate,
                "delay_days": delay,
                "interest": interest
            }

            collection.insert_one(data)

            st.success("Bill saved successfully!")
            st.info(
                f"Delay: {delay} days | Interest: ₹{interest:.2f}"
            )

        except Exception as e:
            st.error(f"Error: {e}")

# =========================================================
# 3️⃣ VIEW RECORDS
# =========================================================

elif menu == "View Records":

    st.subheader("📋 Billing Records")

    with st.form("search_form"):
        col1, col2 = st.columns(2)

        with col1:
            search_bill = st.text_input("Search by Bill Number")

        with col2:
            search_party = st.text_input("Search by Party Name")

        search_btn = st.form_submit_button("Search")

    if search_btn:

        query = {}

        if search_bill:
            query["bill_number"] = search_bill

        if search_party:
            query["party_name"] = {"$regex": search_party, "$options": "i"}

        records = list(collection.find(query, {"_id": 0}))

        if records:
            df = pd.DataFrame(records)

            if "bill_date" in df.columns:
                df["bill_date"] = df["bill_date"].astype(str)

            if "payment_date" in df.columns:
                df["payment_date"] = df["payment_date"].astype(str)

            st.dataframe(df, use_container_width=True)

        else:
            st.info("No records found.")