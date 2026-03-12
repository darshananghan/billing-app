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
    interestable_amount = bill_amount * 100 / 105
    due_date = bill_date + timedelta(days=due_days)
    delay_days = (payment_date - due_date).days

    if delay_days < 0:
        delay_days = 0

    daily_rate = monthly_rate / 30
    interest = interestable_amount  * (daily_rate / 100) * delay_days
    total_amount = bill_amount + interest

    return delay_days, interest, interestable_amount


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
            bill_date_str = st.text_input("Bill Date (DD-MM-YYYY)")
            bill_amount = st.number_input("Bill Amount", value=None, placeholder="Enter amount")
            due_days = st.number_input("Due Days", value=None, placeholder="Enter due days")

        with col2:
            payment_date_str = st.text_input("Payment Date (DD-MM-YYYY)")
            monthly_rate = st.number_input("Monthly Interest Rate (%)", value=None, placeholder="Enter monthly rate")

        calculate_btn = st.form_submit_button("Calculate Interest")

    if calculate_btn:
        try:
            bill_date = datetime.strptime(bill_date_str, "%d-%m-%Y")
            payment_date = datetime.strptime(payment_date_str, "%d-%m-%Y")

            delay, interest, interestable_amount = calculate_interest(
                bill_date, bill_amount, due_days, payment_date, monthly_rate
            )

            st.success(f"Delay Days: {delay}")
            st.success(f"Interestable Amount (GST removed): ₹{interestable_amount:.2f}")
            st.success(f"Interest: ₹{interest:.2f}")

        except:
            st.error("Please enter dates in DD-MM-YYYY format.")
            
            
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
            bill_date_str = st.text_input("Bill Date (DD-MM-YYYY)")
            bill_amount = st.number_input("Bill Amount", value=None, placeholder="Enter amount")
            due_days = st.number_input("Due Days", value=None, placeholder="Enter due days")

        with col2:
            payment_date_str = st.text_input("Payment Date (DD-MM-YYYY)")
            monthly_rate = st.number_input("Monthly Interest Rate (%)", value=None, placeholder="Enter rate")

        save_btn = st.form_submit_button("Calculate & Save")

    if save_btn:
        try:
            bill_date = datetime.strptime(bill_date_str, "%d-%m-%Y")
            payment_date = datetime.strptime(payment_date_str, "%d-%m-%Y")

            delay, interest, interestable_amount = calculate_interest(
                bill_date, bill_amount, due_days, payment_date, monthly_rate
            )

            data = {
                "bill_number": bill_number,
                "party_name": party_name,
                "bill_date": bill_date,
                "bill_amount": bill_amount,
                "interestable_amount": interestable_amount,
                "due_days": due_days,
                "payment_date": payment_date,
                "monthly_rate": monthly_rate,
                "delay_days": delay,
                "interest": interest
            }

            collection.insert_one(data)

            st.success("Bill saved successfully!")

        except ValueError:
            st.error("Invalid date format. Please use DD-MM-YYYY.")
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