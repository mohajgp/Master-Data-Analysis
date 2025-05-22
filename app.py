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

# Normalize key search fields
df['Phone Number'] = df['Phone Number'].str.replace(r'\D', '', regex=True)
df['WHAT IS YOUR NATIONAL ID?'] = df['WHAT IS YOUR NATIONAL ID?'].str.strip()

# Title
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

# Apply Filters
filtered = df[df['County'].isin(selected_counties)]
filtered = filtered[(filtered['Timestamp'] >= pd.to_datetime(start_date)) & (filtered['Timestamp'] <= pd.to_datetime(end_date))]

# === KPI Summary ===
st.markdown("### 📈 Summary KPIs")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Participants", len(filtered))
col2.metric("Registered Businesses", filtered['IS YOUR BUSINESS REGISTERED?'].str.upper().eq("YES").sum())
col3.metric("Disability (Declared)", filtered['DO YOU IDENTIFY AS A PERSON WITH A DISABILITY? (THIS QUESTION IS OPTIONAL AND YOUR RESPONSE WILL NOT AFFECT YOUR ELIGIBILITY FOR THE PROGRAM.)'].str.upper().eq("YES").sum())
col4.metric("Avg Revenue (Good Month)", f"KES {int(pd.to_numeric(filtered['WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY GOOD MONTH'], errors='coerce').mean(skipna=True)):,}")

# === Filtered Participants Table ===
st.markdown(f"### 👥 Filtered Participants: {len(filtered)}")
st.dataframe(filtered.head(200), use_container_width=True)

# === County Summary Table ===
st.markdown("### 📍 Participants Summary by County")

# Add calculated fields
filtered['Is Youth'] = filtered['Age'].apply(lambda x: 18 <= x <= 35 if pd.notnull(x) else False)
filtered['Is Female Youth'] = filtered.apply(lambda x: x['Is Youth'] and x['Gender'] == 'Female', axis=1)

summary = filtered.groupby('County').agg(
    Total_Participants=('Full Name', 'count'),
    Youth_Count=('Is Youth', 'sum'),
    Female_Youth_Count=('Is Female Youth', 'sum')
).reset_index()

summary['% Youth (18–35 yrs)'] = (summary['Youth_Count'] / summary['Total_Participants'] * 100).round(1)
summary['% Female Youths'] = (summary['Female_Youth_Count'] / summary['Total_Participants'] * 100).round(1)

summary_display = summary[['County', 'Total_Participants', '% Youth (18–35 yrs)', '% Female Youths']].sort_values(by='Total_Participants', ascending=False)

st.dataframe(summary_display, use_container_width=True)

# === Download County Summary ===
csv_summary = summary_display.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download County Summary CSV", data=csv_summary, file_name="county_summary.csv", mime="text/csv")
