import streamlit as st
import pandas as pd
import altair as alt

# CONFIG
st.set_page_config(page_title="KNCCI Jiinue Dashboard", layout="wide")

# LOAD CSV from Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0/export?format=csv&id=1gxiQhl4sKKQtlSqJvDZ5qE9WC1MGab6zDmJ88Y0me_0"
df = pd.read_csv(sheet_url)

# CLEAN
df['Phone Number'] = df['Phone Number'].astype(str).str.strip()
df['WHAT IS YOUR NATIONAL ID?'] = df['WHAT IS YOUR NATIONAL ID?'].astype(str).str.strip()
df['IS YOUR BUSINESS REGISTERED?'] = df['IS YOUR BUSINESS REGISTERED?'].fillna("").astype(str)
df['Gender'] = df['Gender'].fillna("Unknown")
df['County'] = df['County'].fillna("Unknown")

# TITLE
st.title("🚀 KNCCI Jiinue Strategic Dashboard")

# SEARCH
st.subheader("🔍 Search Participant")
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

# SUMMARY KPIs
st.markdown("### 📊 Summary Stats")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Participants", len(df))
col2.metric("Registered Businesses", df['IS YOUR BUSINESS REGISTERED?'].str.upper().eq("YES").sum())
col3.metric("Disability Declared", df['DO YOU IDENTIFY AS A PERSON WITH A DISABILITY? (THIS QUESTION IS OPTIONAL AND YOUR RESPONSE WILL NOT AFFECT YOUR ELIGIBILITY FOR THE PROGRAM.)'].str.upper().eq("YES").sum())
col4.metric("Avg Revenue (Good Month)", f"KES {int(df['WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY GOOD MONTH'].fillna(0).astype(float).mean()):,}")

# FILTERS
st.sidebar.header("🎛️ Filter Data")
multi_counties = st.sidebar.multiselect("Filter by County (multi-select)", options=sorted(df['County'].unique()), default=[])
selected_sector = st.sidebar.selectbox("Filter by Sector", options=["All"] + sorted(df['WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?'].dropna().unique()))
selected_gender = st.sidebar.selectbox("Filter by Gender", ["All", "Male", "Female"])

# APPLY FILTERS
filtered_df = df.copy()
if multi_counties:
    filtered_df = filtered_df[filtered_df['County'].isin(multi_counties)]
if selected_sector != "All":
    filtered_df = filtered_df[filtered_df['WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?'] == selected_sector]
if selected_gender != "All":
    filtered_df = filtered_df[filtered_df['Gender'].str.lower() == selected_gender.lower()]

st.markdown(f"### 👥 Filtered Participants: {len(filtered_df)}")
st.dataframe(filtered_df)

# CHARTS
st.markdown("### 📈 Interactive Charts")

# Chart 1: Participants by County
st.subheader("Participants by County")
county_chart = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('count():Q', title='Number of Participants'),
    y=alt.Y('County:N', sort='-x'),
    tooltip=['County', 'count()']
).properties(height=400).interactive()
st.altair_chart(county_chart, use_container_width=True)

# Chart 2: Gender Breakdown
st.subheader("Gender Distribution")
gender_chart = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('Gender:N'),
    y=alt.Y('count():Q', title='Count'),
    color='Gender:N',
    tooltip=['Gender', 'count()']
).properties(width=500)
st.altair_chart(gender_chart, use_container_width=True)

# Chart 3: Registered vs Not
st.subheader("Business Registration Status")
reg_chart = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('IS YOUR BUSINESS REGISTERED?:N', title='Registered?'),
    y=alt.Y('count():Q', title='Count'),
    color='IS YOUR BUSINESS REGISTERED?:N',
    tooltip=['IS YOUR BUSINESS REGISTERED?:N', 'count()']
).properties(width=500)
st.altair_chart(reg_chart, use_container_width=True)

# EXPORT
st.markdown("### 📥 Download Filtered Data")
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", data=csv, file_name="KNCCI_filtered_data.csv", mime="text/csv")
