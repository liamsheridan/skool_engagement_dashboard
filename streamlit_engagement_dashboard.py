import plotly.express as px
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import openpyxl
from datetime import datetime, timedelta
import os
from PIL import Image
import matplotlib.pyplot as plt

# Input fields for uploading new data
st.sidebar.subheader("Upload Community Data CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type="csv")

if uploaded_file is not None:
    # Extract community identifier from file name for dynamic URL
    community_identifier = uploaded_file.name.split('.')[0]
    st.experimental_set_query_params(community=community_identifier)
    with st.spinner("Loading data, please wait..."):
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            df = None
else:
    st.error("Please upload a CSV file to proceed.")
    df = None

# Only proceed if df is defined
if df is not None:
    # Convert Post Date to datetime
    try:
        df['Post Date'] = pd.to_datetime(df['Post Date'], format="%d/%m/%Y")
    except Exception as e:
        st.error(f"Error converting Post Date: {e}")
        st.stop()  # Stop execution if no valid data is available

st.markdown("""
    <style>
        @media print {
            h1, h2, h3, h4, h5, h6, p, div, table, thead, tbody, tfoot, tr, th, td {
                page-break-inside: avoid;
            }
            .page-break {
                page-break-before: always;
            }
            .chart-container {
                page-break-inside: avoid;
                page-break-before: auto;
                page-break-after: auto;
                margin-bottom: 20px; /* Reduced spacing for printing */
            }
            body {
                -webkit-print-color-adjust: exact;
                font-size: 14px; /* Adjust font size for readability in print */
            }
            table {
                page-break-inside: avoid;
                margin-bottom: 20px;
            }
        }
        body {
            font-family: Arial, sans-serif;
        }
        h1 {
            margin-bottom: 0px !important;
            text-align: center;
            font-weight: bold;
            font-size: 28px; /* Larger font for main title */
        }
        h2 {
            text-align: center;
            font-weight: bold;
            font-size: 22px;
            margin-bottom: 5px;
            margin-top: 10px;
        }
        h3 {
            text-align: center;
            margin-top: 0px !important;
            margin-bottom: 10px;
            font-size: 18px; /* Consistent subheading size */
        }
        h4.leaderboard-header {
            text-align: center;
            margin-top: 5px;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 16px;
        }
        .leaderboard-table {
            margin-top: 0px;
            page-break-inside: avoid;
        }
        table.custom-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        th, td {
            border: 1px solid #444;
            padding: 8px;
            text-align: center;
            font-size: 14px;
        }
        th {
            background-color: #444;
            color: white;
            height: 40px;
            text-align: center;
        }
        td img {
            width: 25px;
            height: 25px;
            border-radius: 50%;
        }
        th.rank, td.rank {
            width: 60px;
        }
        th.profile-picture, td.profile-picture {
            width: 60px;
        }
        th.name, td.name {
            width: 200px;
        }
        th.metric, td.metric {
            width: 50px;
        }
        caption {
            font-size: 2em;
            margin-bottom: 10px;
            font-weight: bold;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# Streamlit App
st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>Skool Community Post Engagement Dashboard</h1>",
            unsafe_allow_html=True)

# Month Filter
if df is not None:
    month_filter = st.sidebar.selectbox("Select Month", options=[
        'All'] + df['Post Date'].dt.strftime('%B %Y').unique().tolist())
    if month_filter != 'All':
        df = df[df['Post Date'].dt.strftime('%B %Y') == month_filter]
else:
    st.warning("Please upload a valid CSV file to proceed.")


# Posts by Day

def posts_by_day(df):
    df['Day'] = df['Post Date'].dt.date
    daily_posts = df.groupby(
        ['Day', 'Category']).size().reset_index(name='Counts')

    st.markdown("<h2 style='text-align: center;'>Posts by Day</h2>",
                unsafe_allow_html=True)

    # Create a pivot table for stacked bar chart
    daily_pivot = daily_posts.pivot(
        index='Day', columns='Category', values='Counts').fillna(0)
    daily_pivot.reset_index(inplace=True)

    # Create Plotly figure for stacked bar chart
    fig = go.Figure()
    color_sequence = px.colors.qualitative.Plotly
    for i, category in enumerate(daily_pivot.columns[1:]):
        fig.add_trace(go.Bar(
            x=daily_pivot['Day'],
            y=daily_pivot[category],
            name=category,
            marker_color=color_sequence[i % len(color_sequence)],
            hovertext=daily_pivot.apply(lambda row: f"{row['Day']}, {
                                        int(row[category])}", axis=1),
            hoverinfo='text'
        ))

    # Update layout for better readability
    fig.update_layout(
        xaxis=dict(title="Day", tickfont=dict(size=16)),
        yaxis=dict(title="Number of Posts", titlefont=dict(
            size=16), tickfont=dict(size=16)),
        barmode='stack',
        template="plotly_dark",
        margin=dict(t=50, b=50),
        height=400
    )

    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.plotly_chart(fig)
    st.markdown("</div>", unsafe_allow_html=True)

# Posts by Week


def posts_by_time_period(df):
    df['Week'] = df['Post Date'].dt.isocalendar().week
    df['Year'] = df['Post Date'].dt.year
    weekly_posts = df.groupby(
        ['Year', 'Week', 'Category']).size().reset_index(name='Counts')
    weekly_posts['Week_Start_Date'] = weekly_posts.apply(
        lambda row: datetime.strptime(f'{row.Year}-W{row.Week}-1', "%Y-W%W-%w"), axis=1
    )

    st.markdown("<h2 style='text-align: center;'>Posts by Week</h2>",
                unsafe_allow_html=True)

    # Create a pivot table for stacked bar chart
    weekly_pivot = weekly_posts.pivot(
        index=['Year', 'Week', 'Week_Start_Date'], columns='Category', values='Counts').fillna(0)
    weekly_pivot.reset_index(inplace=True)

    # Create Plotly figure for stacked bar chart
    fig = go.Figure()
    color_sequence = px.colors.qualitative.Plotly
    for i, category in enumerate(weekly_pivot.columns[3:]):
        fig.add_trace(go.Bar(
            x=weekly_pivot['Week'],
            y=weekly_pivot[category],
            name=category,
            marker_color=color_sequence[i % len(color_sequence)],
            hovertext=weekly_pivot.apply(
                lambda row: f"w/c {row['Week_Start_Date'].strftime('%d %b %Y')}, {int(row[category])}", axis=1),
            hoverinfo='text'
        ))

    # Update layout for better readability
    fig.update_layout(
        xaxis=dict(title="Week", tickfont=dict(size=16)),
        yaxis=dict(title="Number of Posts", titlefont=dict(
            size=16), tickfont=dict(size=16)),
        barmode='stack',
        template="plotly_dark",
        margin=dict(t=50, b=50),
        height=400
    )

    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.plotly_chart(fig)
    st.markdown("</div>", unsafe_allow_html=True)


# Top Performing Posts

def top_performing_posts(df):
    df['Total Engagement'] = df['Likes'].astype(
        int) + df['Comments'].astype(int)
    top_posts = df.sort_values(by='Total Engagement', ascending=False).head(10)
    st.markdown("<div class='page-break'><h2 style='text-align: center;'>Top Performing Posts</h2></div>",
                unsafe_allow_html=True)

    # Top 5 Performing Posts by Total Engagement
    top_5_posts = top_posts.head(5)
    st.markdown("<h3 style='text-align: center;'>Top 5 Performing Posts by Total Engagement</h3>",
                unsafe_allow_html=True)
    st.table(top_5_posts[['Name', 'Title', 'Likes',
             'Comments', 'Total Engagement']].reset_index(drop=True))

    # Top 5 Performing Posts by Total Engagement (Excluding Community Owner)
    community_owner = st.sidebar.text_input(
        "Enter Community Owner Name to Exclude:")
    if community_owner:
        top_posts_excluding_owner = df[df['Name'] != community_owner].sort_values(
            by='Total Engagement', ascending=False).head(10)
        top_5_posts_excluding_owner = top_posts_excluding_owner.head(5)
        st.markdown(
            "<h3 style='text-align: center;'>Top 5 Performing Posts by Total Engagement (Excluding Community Owner)</h3>", unsafe_allow_html=True)
        st.table(top_5_posts_excluding_owner[[
                 'Name', 'Title', 'Likes', 'Comments', 'Total Engagement']].reset_index(drop=True))

# Posts by Category


def posts_by_category(df):
    category_count = df['Category'].value_counts(
    ).sort_values(ascending=False).reset_index()
    category_count.columns = ['Category', 'Count']

    st.markdown("<div class='chart-container'><h2 style='text-align: center;'>Posts by Category</h2></div>",
                unsafe_allow_html=True)

    # Use Plotly to create a bar chart with customization and emoji support
    fig = px.bar(category_count, x='Category', y='Count', text='Count',
                 color='Category', color_discrete_sequence=px.colors.qualitative.Plotly)
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title="Number of Posts",
        xaxis_title="Categories",
        template="plotly_dark",
        font=dict(size=16),
        margin=dict(t=50, b=100)
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')

    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.plotly_chart(fig)
    st.markdown("</div>", unsafe_allow_html=True)

# Add Pie Chart for Posts by Owner vs Members


def posts_by_owner_vs_members(df):
    st.markdown("<div class='chart-container'><h2 style='text-align: center;'>Posts by Owner vs Members</h2></div>", unsafe_allow_html=True)

    owner_name = st.sidebar.text_input(
        "Enter Community Owner Name for Pie Chart:")
    if owner_name and df is not None:
        try:
            # Check if the 'Name' column exists
            if 'Name' in df.columns:
                owner_posts_count = df[df['Name'] == owner_name].shape[0]
                members_posts_count = df[df['Name'] != owner_name].shape[0]

                # Create data for the pie chart
                pie_data = pd.DataFrame({
                    'User Type': ['Owner', 'Members'],
                    'Count': [owner_posts_count, members_posts_count]
                })

                # Create and display the pie chart
                pie_fig = px.pie(pie_data, values='Count', names='User Type',
                                 color_discrete_sequence=px.colors.qualitative.Plotly)
                pie_fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    textfont_size=18,  # Make percentage text bigger
                    textfont_color='white'  # Set text color to white
                )
                pie_fig.update_layout(showlegend=False)  # Remove the legend
                st.plotly_chart(pie_fig)
            else:
                st.error("The required column 'Name' does not exist in the data.")
        except Exception as e:
            st.error(f"An error occurred while generating the pie chart: {e}")
    else:
        st.warning(
            "Please enter a valid community owner name and ensure a CSV file is uploaded.")

# Users Engagement Leaderboard


def users_engagement_leaderboard(df, metric='Posts'):
    if metric == "Posts":
        leaderboard = df['Name'].value_counts().reset_index()
        leaderboard.columns = ['Name', 'Posts']
    elif metric == "Likes":
        leaderboard = df.groupby('Name')['Likes'].sum(
        ).sort_values(ascending=False).reset_index()
    elif metric == "Comments":
        leaderboard = df.groupby('Name')['Comments'].sum(
        ).sort_values(ascending=False).reset_index()
    elif metric == "Total Engagement":
        df['Total Engagement'] = df['Likes'].astype(
            int) + df['Comments'].astype(int)
        leaderboard = df.groupby('Name')['Total Engagement'].sum(
        ).sort_values(ascending=False).reset_index()

    leaderboard = leaderboard.merge(
        df[['Name', 'Profile Picture']].drop_duplicates(), on='Name', how='left').head(20)
    leaderboard.reset_index(drop=True, inplace=True)
    leaderboard.insert(0, 'Rank', leaderboard.index + 1)

    # Display leaderboard in the same format as previously with profile pictures
    st.write("<style>"
             "table {width: 100%; border-collapse: collapse;}"
             "th, td {border: 1px solid #444; padding: 8px; text-align: center; font-size: 14px;}"
             "th {background-color: #444; color: white; height: 40px; text-align: center;}"
             "td img {width: 25px; height: 25px; border-radius: 50%;}"
             "th.rank, td.rank {width: 60px;}"
             "th.profile-picture, td.profile-picture {width: 60px;}"
             "th.name, td.name {width: 200px;}"
             "th.metric, td.metric {width: 50px;}"
             "caption {font-size: 2em; margin-bottom: 10px; font-weight: bold; text-align: center;}"
             "</style>", unsafe_allow_html=True)
    st.write("<div class='no-page-break' style='margin-top: 5px;'><table class='custom-table no-page-break'>",
             unsafe_allow_html=True)
    st.write("<tbody>", unsafe_allow_html=True)
    for _, row in leaderboard.iterrows():
        st.write(f"<tr>"
                 f"<td class='rank'>{row['Rank']}</td>"
                 f"<td class='profile-picture'><img src='{
                     row['Profile Picture']}'></td>"
                 f"<td class='name'>{row['Name']}</td>"
                 f"<td class='metric'>{row[metric]}</td>"
                 f"</tr>", unsafe_allow_html=True)
    st.write("</tbody></table></div>", unsafe_allow_html=True)

# Run Analysis in Streamlit


st.markdown("<div class='full-page'>", unsafe_allow_html=True)

# Charts and Headers - Page 1
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
posts_by_day(df)
posts_by_time_period(df)
st.markdown("</div>", unsafe_allow_html=True)

# Posts by Category and Posts by Owner vs Members - Page 2
st.markdown("<div class='page-break full-page'>", unsafe_allow_html=True)
posts_by_category(df)
posts_by_owner_vs_members(df)
st.markdown("</div>", unsafe_allow_html=True)

# Top Performing Posts - Page 3
st.markdown("<div class='full-page'>", unsafe_allow_html=True)
top_performing_posts(df)
st.markdown("</div>", unsafe_allow_html=True)

# User Engagement Leaderboards - Page 4
st.markdown("<div class='page-break full-page'>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>User Engagement Leaderboard</h2>",
            unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -10px; margin-bottom: 5px;'>Top 20 Members by</h3>",
            unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Posts and Likes leaderboards side by side
with col1:
    st.markdown("<h4 class='leaderboard-header' style='text-align: center;'>Posts</h4>",
                unsafe_allow_html=True)
    st.markdown("<div class='leaderboard-table no-page-break'>",
                unsafe_allow_html=True)
    users_engagement_leaderboard(df, metric='Posts')
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<h4 class='leaderboard-header' style='text-align: center;'>Likes</h4>",
                unsafe_allow_html=True)
    st.markdown("<div class='leaderboard-table no-page-break'>",
                unsafe_allow_html=True)
    users_engagement_leaderboard(df, metric='Likes')
    st.markdown("</div>", unsafe_allow_html=True)

# Add headers again for page 5
st.markdown("<div class='page-break full-page'>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>User Engagement Leaderboard</h2>",
            unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -10px; margin-bottom: 5px;'>Top 20 Members by</h3>",
            unsafe_allow_html=True)

# Comments and Total Engagement leaderboards side by side
col3, col4 = st.columns(2)

with col3:
    st.markdown("<h4 class='leaderboard-header' style='text-align: center;'>Comments</h4>",
                unsafe_allow_html=True)
    st.markdown("<div class='leaderboard-table no-page-break'>",
                unsafe_allow_html=True)
    users_engagement_leaderboard(df, metric='Comments')
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<h4 class='leaderboard-header' style='text-align: center;'>Total Engagement</h4>",
                unsafe_allow_html=True)
    st.markdown("<div class='leaderboard-table no-page-break'>",
                unsafe_allow_html=True)
    users_engagement_leaderboard(df, metric='Total Engagement')
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
