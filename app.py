import streamlit as st
import pandas as pd

st.set_page_config(page_title="🚀 KNCCI Jiinue Strategic Dashboard", layout="wide")

# --- Load and cache Google Sheet ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0/export?format=csv&id=1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0"
    df = pd.read_csv(url, dtype=str)
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
    df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['Gender'] = df['Gender'].str.title()
    return df

df = load_data()

# Normalize key fields
df['Phone Number'] = df['Phone Number'].str.replace(r'\D', '', regex=True)
df['WHAT IS YOUR NATIONAL ID?'] = df['WHAT IS YOUR NATIONAL ID?'].str.strip()

# === Diagnostic Outputs (Optional) ===
st.sidebar.markdown("### 🧪 Data Diagnostics")
st.sidebar.write(f"Total raw rows: {len(df)}")
st.sidebar.write(f"Missing timestamps: {df['Timestamp'].isna().sum()}")
st.sidebar.write(f"Missing county values: {df['County'].isna().sum()}")
st.sidebar.write(f"Unique counties found: {df['County'].nunique()}")

# --- Title ---
st.title("🚀 KNCCI Jiinue Strategic Dashboard")

# === Search Section ===
st.subheader("🔍 Quick Participant Search")
col1, col2 = st.columns(2)
search_id = col1.text_input("Search by National ID (digits only)")
search_phone = col2.text_input("Or Search by Phone Number (digits only)")

if search_id:
    sid = ''.join(filter(str.isdigit, search_id.strip()))
    res = df[df['WHAT IS YOUR NATIONAL ID?'] == sid]
    st.write(res if not res.empty else "❌ No match found.")
elif search_phone:
    sphone = ''.join(filter(str.isdigit, search_phone.strip()))
    res = df[df['Phone Number'] == sphone]
    st.write(res if not res.empty else "❌ No match found.")

# === Sidebar Filters ===
st.sidebar.header("🎛️ Filter Participants")
counties = sorted(df['County'].dropna().unique())
selected_counties = st.sidebar.multiselect("Select Counties", counties, default=counties)

# Date Range
st.sidebar.markdown("### 🗓️ Date Range")
min_date = df['Timestamp'].min()
max_date = df['Timestamp'].max()
start_date, end_date = st.sidebar.date_input("Filter by Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# === Apply Filters ===
filtered = df[df['County'].isin(selected_counties)]
filtered = filtered[(filtered['Timestamp'] >= pd.to_datetime(start_date)) & (filtered['Timestamp'] <= pd.to_datetime(end_date))]

# === Summary KPIs ===
st.markdown("### 📈 Summary KPIs")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("All Participants", len(df))
col2.metric("Filtered Participants", len(filtered))
col3.metric("Registered Businesses", filtered['IS YOUR BUSINESS REGISTERED?'].str.upper().eq("YES").sum())
col4.metric("Disability (Declared)", filtered['DO YOU IDENTIFY AS A PERSON WITH A DISABILITY? (THIS QUESTION IS OPTIONAL AND YOUR RESPONSE WILL NOT AFFECT YOUR ELIGIBILITY FOR THE PROGRAM.)'].str.upper().eq("YES").sum())
col5.metric("Avg Revenue (Good Month)", f"KES {int(pd.to_numeric(filtered['WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY GOOD MONTH'], errors='coerce').mean(skipna=True)):,}")

# === Clean Summary Table by County ===
st.markdown("### 📍 County Summary")

filtered['Is Youth'] = filtered['Age'].apply(lambda x: 18 <= x <= 35 if pd.notnull(x) else False)
filtered['Is Female Youth'] = filtered.apply(lambda x: x['Is Youth'] and x['Gender'] == 'Female', axis=1)

summary = filtered.groupby('County').agg(
    Total_Participants=('Full Name', 'count'),
    Youth_Count=('Is Youth', 'sum'),
    Female_Youth_Count=('Is Female Youth', 'sum')
).reset_index()

summary['% Youths (18–35 yrs)'] = (summary['Youth_Count'] / summary['Total_Participants'] * 100).round(1)
summary['% Female Youths (18–35 yrs)'] = (summary['Female_Youth_Count'] / summary['Total_Participants'] * 100).round(1)

# Rename and organize columns
summary_display = summary[['County', 'Total_Participants', '% Youths (18–35 yrs)', '% Female Youths (18–35 yrs)']].copy()
summary_display.columns = ['County', 'Number of TA Participants', 'Percentage of Youths (18–35 yrs)', 'Percentage of Female Youths (18–35 yrs)']
summary_display = summary_display.sort_values(by='Number of TA Participants', ascending=False)

st.dataframe(summary_display, use_container_width=True)

# === Download CSV Button ===
csv = summary_display.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download County Summary CSV", data=csv, file_name="county_summary.csv", mime="text/csv")
