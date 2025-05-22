import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="KNCCI Jiinue Dashboard", layout="wide")

# --- Load and cache Google Sheet ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0/export?format=csv&id=1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0"
    df = pd.read_csv(url, dtype=str)  # force all as strings
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')  # convert timestamp
    return df

df = load_data()

# --- Normalize Key Columns ---
df['Phone Number'] = df['Phone Number'].str.replace(r'\D', '', regex=True)
df['WHAT IS YOUR NATIONAL ID?'] = df['WHAT IS YOUR NATIONAL ID?'].str.strip()

# --- Title ---
st.title("🚀 KNCCI Jiinue Strategic Dashboard")

# --- Search Section ---
st.subheader("🔍 Quick Participant Search")
col1, col2 = st.columns(2)
search_id = col1.text_input("Search by National ID (digits only)")
search_phone = col2.text_input("Or Search by Phone Number (digits only)")

if search_id:
    search_id_clean = ''.join(filter(str.isdigit, search_id.strip()))
    result = df[df['WHAT IS YOUR NATIONAL ID?'] == search_id_clean]
    st.write(result if not result.empty else "❌ No match found.")
elif search_phone:
    search_phone_clean = ''.join(filter(str.isdigit, search_phone.strip()))
    result = df[df['Phone Number'] == search_phone_clean]
    st.write(result if not result.empty else "❌ No match found.")

# --- KPI Summary ---
st.markdown("### 📈 Summary KPIs")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Participants", len(df))
col2.metric("Registered Businesses", df['IS YOUR BUSINESS REGISTERED?'].str.upper().eq("YES").sum())
col3.metric("Disability (Declared)", df['DO YOU IDENTIFY AS A PERSON WITH A DISABILITY? (THIS QUESTION IS OPTIONAL AND YOUR RESPONSE WILL NOT AFFECT YOUR ELIGIBILITY FOR THE PROGRAM.)'].str.upper().eq("YES").sum())
col4.metric("Avg Revenue (Good Month)", f"KES {int(pd.to_numeric(df['WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY GOOD MONTH'], errors='coerce').mean(skipna=True)):,}")

# --- Sidebar Filters ---
st.sidebar.header("🎛️ Filter Data")
county_options = sorted(df['County'].dropna().unique())
selected_counties = st.sidebar.multiselect("Select Counties", options=county_options, default=county_options)
selected_sector = st.sidebar.selectbox("Sector", options=["All"] + sorted(df['WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?'].dropna().unique()))
selected_gender = st.sidebar.selectbox("Gender", options=["All", "Male", "Female"])

# Date Range Filter
st.sidebar.markdown("### 🗓️ Date Range Filter")
min_date = df['Timestamp'].min()
max_date = df['Timestamp'].max()
start_date, end_date = st.sidebar.date_input("Filter by Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# --- Apply Filters ---
filtered = df[df['County'].isin(selected_counties)]
if selected_sector != "All":
    filtered = filtered[filtered['WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?'] == selected_sector]
if selected_gender != "All":
    filtered = filtered[filtered['Gender'].str.lower() == selected_gender.lower()]
filtered = filtered[(filtered['Timestamp'] >= pd.to_datetime(start_date)) & (filtered['Timestamp'] <= pd.to_datetime(end_date))]

# --- Show Filtered Table ---
st.markdown(f"### 👥 Filtered Participants: {len(filtered)}")
st.dataframe(filtered.head(200), use_container_width=True)

# --- Charts ---
st.markdown("### 📊 Charts")

with st.expander("📍 Participants by County"):
    chart = alt.Chart(filtered).mark_bar().encode(
        y=alt.Y('County:N', sort='-x'),
        x=alt.X('count():Q', title='Participants'),
        tooltip=['County', 'count()']
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

with st.expander("👫 Gender Breakdown"):
    gender_chart = alt.Chart(filtered).mark_bar().encode(
        x=alt.X('Gender:N'),
        y=alt.Y('count():Q'),
        color='Gender:N',
        tooltip=['Gender', 'count()']
    )
    st.altair_chart(gender_chart, use_container_width=True)

with st.expander("📋 Registration Status"):
    reg_chart = alt.Chart(filtered).mark_bar().encode(
        x=alt.X('IS YOUR BUSINESS REGISTERED?:N', title="Registered?"),
        y=alt.Y('count():Q'),
        color='IS YOUR BUSINESS REGISTERED?:N'
    )
    st.altair_chart(reg_chart, use_container_width=True)

with st.expander("📅 Registrations Over Time"):
    daily = filtered.copy()
    daily['Date'] = daily['Timestamp'].dt.date
    daily_count = daily.groupby('Date').size().reset_index(name='Registrations')
    date_chart = alt.Chart(daily_count).mark_line(point=True).encode(
        x='Date:T',
        y='Registrations:Q',
        tooltip=['Date:T', 'Registrations']
    ).properties(height=300)
    st.altair_chart(date_chart, use_container_width=True)

# --- Export ---
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Filtered CSV", data=csv, file_name="filtered_participants.csv", mime="text/csv")
