import streamlit as st
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="KNCCI Jiinue Dashboard", layout="wide")

# --- LOAD DATA FROM GOOGLE SHEET ---
sheet_url = "https://docs.google.com/spreadsheets/d/1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0/export?format=csv&id=1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0"
df = pd.read_csv(sheet_url)

# --- CLEAN ---
df['Phone Number'] = df['Phone Number'].astype(str).str.strip()
df['WHAT IS YOUR NATIONAL ID?'] = df['WHAT IS YOUR NATIONAL ID?'].astype(str).str.strip()

# --- TITLE ---
st.title("📊 KNCCI Jiinue Participant Dashboard")

# --- SEARCH ---
st.subheader("🔍 Quick Lookup")
col1, col2 = st.columns(2)
search_id = col1.text_input("Search by National ID")
search_phone = col2.text_input("Search by Phone Number")

if search_id:
    result = df[df['WHAT IS YOUR NATIONAL ID?'] == search_id]
    st.success("Match found by ID!" if not result.empty else "No match found.")
    st.write(result)
elif search_phone:
    result = df[df['Phone Number'] == search_phone]
    st.success("Match found by Phone!" if not result.empty else "No match found.")
    st.write(result)

# --- KPIs ---
st.markdown("### 📈 Summary Statistics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Participants", len(df))
col2.metric("Registered Businesses", df['IS YOUR BUSINESS REGISTERED?'].str.upper().eq("YES").sum())
col3.metric("Disability Declared", df['DO YOU IDENTIFY AS A PERSON WITH A DISABILITY? (THIS QUESTION IS OPTIONAL AND YOUR RESPONSE WILL NOT AFFECT YOUR ELIGIBILITY FOR THE PROGRAM.)'].str.upper().eq("YES").sum())
col4.metric("Avg Monthly Revenue (Good Month)", f"KES {int(df['WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY GOOD MONTH'].fillna(0).astype(float).mean()):,}")

# --- FILTERING SECTION ---
st.sidebar.header("📂 Filter Participants")
counties = ["All"] + sorted(df['County'].dropna().unique().tolist())
sectors = ["All"] + sorted(df['WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?'].dropna().unique().tolist())
genders = ["All", "Male", "Female"]

selected_county = st.sidebar.selectbox("County", counties)
selected_sector = st.sidebar.selectbox("Sector", sectors)
selected_gender = st.sidebar.selectbox("Gender", genders)

filtered_df = df.copy()
if selected_county != "All":
    filtered_df = filtered_df[filtered_df['County'] == selected_county]
if selected_sector != "All":
    filtered_df = filtered_df[filtered_df['WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?'] == selected_sector]
if selected_gender != "All":
    filtered_df = filtered_df[filtered_df['Gender'].str.lower() == selected_gender.lower()]

st.markdown(f"### 👥 Filtered Participants: {len(filtered_df)}")
st.dataframe(filtered_df)

# --- EXPORT ---
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Filtered CSV", data=csv, file_name="filtered_participants.csv", mime="text/csv")
