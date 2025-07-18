import streamlit as st
import pandas as pd
import plotly.express as px

st.title("TV Channel Revenue Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

# Function to load and process data
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df['Sale Placement Date'] = pd.to_datetime(df['Sale Placement Date'])
    df['Month'] = df['Sale Placement Date'].dt.strftime('%B')
    df['Day'] = df['Sale Placement Date'].dt.date

    def get_daypart(hour):
        if 5 <= hour < 12:
            return 'Morning'
        elif 12 <= hour < 17:
            return 'Afternoon'
        elif 17 <= hour < 21:
            return 'Evening'
        else:
            return 'Night'

    def get_time_slot(hour):
        return f"{hour:02d}:00-{(hour+1):02d}:00"

    df['Hour'] = df['Sale Placement Date'].dt.hour
    df['Daypart'] = df['Hour'].apply(get_daypart)
    df['Time_Slot'] = df['Hour'].apply(get_time_slot)
    return df

# Stop execution until a file is uploaded
if uploaded_file is None:
    st.warning("Please upload an Excel file to continue.")
    st.stop()

# Load data
df = load_data(uploaded_file)

# Sidebar filters
products = df['Product Line (no hierarchy)'].unique()
selected_product = st.sidebar.selectbox("Select Product", options=products)
months = df['Month'].unique()
selected_months = st.sidebar.multiselect("Select Months", options=months, default=list(months))

filtered_df = df[
    (df['Product Line (no hierarchy)'] == selected_product) &
    (df['Month'].isin(selected_months))
]

# Flatten revenue data
channel_cols = ['TV Channel 1', 'TV Channel 2', 'TV Channel 3', 'TV Channel 4']
revenue_cols = ['TV Channel 1 £', 'TV Channel 2 £', 'TV Channel 3 £', 'TV Channel 4 £']

flat_data = []
for i in range(1, 5):
    temp = filtered_df[[f'TV Channel {i}', f'TV Channel {i} £', 'Day', 'Daypart', 'Time_Slot', 'Hour']].copy()
    temp.columns = ['Channel', 'Revenue', 'Day', 'Daypart', 'Time_Slot', 'Hour']
    flat_data.append(temp)

channels_df = pd.concat(flat_data)
channels_df = channels_df.dropna(subset=['Channel'])

# Section 1: MER by Channel
st.subheader("MER by Channel")
revenue_by_channel = channels_df.groupby('Channel')['Revenue'].sum().reset_index()
revenue_by_channel = revenue_by_channel.sort_values('Revenue', ascending=False)

st.write("**Enter Cost for Each Channel:**")
cost_inputs = {}
col1, col2 = st.columns(2)

for i, row in revenue_by_channel.iterrows():
    channel = row['Channel']
    with col1 if i % 2 == 0 else col2:
        cost_inputs[channel] = st.number_input(
            f"Cost for {channel}",
            min_value=0.0,
            value=0.0,
            step=100.0,
            key=f"cost_{channel}"
        )

mer_data = []
for channel in revenue_by_channel['Channel']:
    revenue = revenue_by_channel[revenue_by_channel['Channel'] == channel]['Revenue'].iloc[0]
    cost = cost_inputs[channel]
    mer = revenue / cost if cost > 0 else 0
    mer_data.append({'Channel': channel, 'Revenue': revenue, 'Cost': cost, 'MER': mer})

mer_df = pd.DataFrame(mer_data).sort_values('MER', ascending=False)
mer_df_display = mer_df.copy()
mer_df_display['Revenue'] = mer_df_display['Revenue'].apply(lambda x: f"£{x:,.2f}")
mer_df_display['Cost'] = mer_df_display['Cost'].apply(lambda x: f"£{x:,.2f}")
mer_df_display['MER'] = mer_df_display['MER'].apply(lambda x: f"{x:.2f}")

st.dataframe(mer_df_display, use_container_width=True)

# Section 2: Daily Revenue by Channel
st.subheader("Daily Revenue by Channel")
daily_rev = channels_df.groupby(['Day', 'Channel'])['Revenue'].sum().reset_index()
st.dataframe(daily_rev)

# Section 3: Revenue by Time Slot by Channel
st.subheader("Revenue by Time Slot by Channel")
timeslot_filtered = channels_df[~channels_df['Channel'].str.contains('web', case=False, na=False)]
timeslot_chart = timeslot_filtered.groupby(['Time_Slot', 'Channel', 'Hour'])['Revenue'].sum().reset_index()
timeslot_chart = timeslot_chart.sort_values('Hour')
fig1 = px.bar(timeslot_chart, x='Time_Slot', y='Revenue', color='Channel', barmode='group')
fig1.update_xaxes(tickangle=45)
st.plotly_chart(fig1)

# Section 4: Top 10 Revenue Channels
st.subheader("Top 10 Revenue Channels")
top10_filtered = revenue_by_channel[~revenue_by_channel['Channel'].str.contains('web', case=False, na=False)]
top10 = top10_filtered.sort_values(by='Revenue', ascending=False).head(10)
fig2 = px.bar(top10, x='Revenue', y='Channel', orientation='h')
st.plotly_chart(fig2)
