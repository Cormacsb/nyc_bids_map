import pandas as pd
import plotly.graph_objects as go
import os

# Create plots directory if it doesn't exist
if not os.path.exists('plots'):
    os.makedirs('plots')

# Constants
FINANCIAL_COLUMNS = [
    'Sanitation expenses',
    'Marketing, holiday lighting, and special event expenses',
    'Public safety expenses',
    'Streetscape & beautification expenses',
    'Other program expenses',
    'Capital improvement expenses',
    'Outside contractor expenses',
    'Salaries',
    'Insurance costs',
    'Rent and utilities',
    'Supplies and equipment costs',
    'Other G&A expenses'
]

# Borough color mapping
BOROUGH_COLORS = {
    'MN': '#1f77b4',  # Manhattan - blue
    'BK': '#2ca02c',  # Brooklyn - green
    'BX': '#ff7f0e',  # Bronx - orange
    'QN': '#d62728',  # Queens - red
    'SI': '#9467bd'   # Staten Island - purple
}

# Load and validate data
bid_data = pd.read_csv('BIDs/FY20_BID_Trends_Report_Data_20250110.csv')
bid_data['Total_Financial'] = bid_data[FINANCIAL_COLUMNS].sum(axis=1)

# Validate totals
mismatch_mask = abs(bid_data['Total_Financial'] - bid_data['Total expenses']) > 10
if mismatch_mask.any():
    mismatched_rows = bid_data[mismatch_mask]
    print("\nMismatched values:")
    for idx, row in mismatched_rows.iterrows():
        print(f"BID: {row['BID Name:']} | Difference: ${row['Total_Financial'] - row['Total expenses']:,.2f}")
    raise ValueError('Total financial differs from total expenses by more than $10')

# Calculate metrics
bid_data['Expense_per_linear_foot'] = bid_data['Total expenses'] / bid_data['Service Area (Linear Feet)']

# Create scatter plot (Total Expenses vs Cost per Linear Foot)
fig_scatter = go.Figure()

# Add traces for each borough
for borough in BOROUGH_COLORS:
    borough_data = bid_data[bid_data['Borough'] == borough]
    fig_scatter.add_trace(go.Scatter(
        x=borough_data['Total expenses'],
        y=borough_data['Expense_per_linear_foot'],
        mode='markers+text',
        text=borough_data['BID Name:'],
        textposition='top center',
        name=borough,
        marker=dict(
            size=10,
            color=BOROUGH_COLORS[borough],
            opacity=0.7
        ),
        hovertemplate="<b>%{text}</b><br>" +
                     "Borough: " + borough + "<br>" +
                     "Total Expenses: $%{x:,.2f}<br>" +
                     "Cost per Linear Foot: $%{y:.2f}<br>" +
                     "<extra></extra>"
    ))

fig_scatter.update_layout(
    title="BID Total Expenses vs Cost per Linear Foot by Borough (Log Scale)",
    xaxis_title="Total Expenses ($)",
    yaxis_title="Cost per Linear Foot ($)",
    width=1500,
    height=800,
    showlegend=True,
    xaxis_type="log",
    yaxis_type="log",
    legend=dict(
        title="Borough",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01
    ),
    xaxis=dict(
        type="log",
        tickformat="$,.0f",
        tickvals=[1e5, 2e5, 4e5, 7e5, 1e6, 2e6, 4e6, 7e6, 1e7, 2e7],  # Custom tick values
        tickangle=45,
        tickfont=dict(size=10)
    )
)

fig_scatter.update_yaxes(tickformat="$,.2f")
fig_scatter.show()

# Save scatter plot
fig_scatter.write_html("plots/bid_expenses_vs_linear_foot.html")

# Create regular histogram of cost per linear foot
fig_hist_linear = go.Figure()

# Create histogram trace for each borough
for borough in BOROUGH_COLORS:
    borough_data = bid_data[bid_data['Borough'] == borough]
    fig_hist_linear.add_trace(go.Histogram(
        x=borough_data['Expense_per_linear_foot'],
        nbinsx=20,
        name=borough,
        marker_color=BOROUGH_COLORS[borough],
        hovertemplate=f"Borough: {borough}<br>Range: $%{{x:.2f}}<br>Count: %{{y}}<extra></extra>"
    ))

fig_hist_linear.update_layout(
    title="Distribution of Cost per Linear Foot by Borough",
    xaxis_title="Cost per Linear Foot ($)",
    yaxis_title="Number of BIDs",
    width=1500,
    height=800,
    bargap=0.1,
    barmode='stack',
    showlegend=True,
    legend=dict(
        title="Borough",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01
    )
)

fig_hist_linear.update_xaxes(tickformat="$,.2f")
fig_hist_linear.show()

# Save histograms
fig_hist_linear.write_html("plots/cost_per_foot_distribution.html")

# Create detailed histogram with $25 bins up to $625
fig_hist_detailed = go.Figure()

# Create detailed histogram trace for each borough
for borough in BOROUGH_COLORS:
    borough_data = bid_data[bid_data['Borough'] == borough]
    fig_hist_detailed.add_trace(go.Histogram(
        x=borough_data['Expense_per_linear_foot'],
        xbins=dict(
            start=0,
            end=625,
            size=25
        ),
        name=borough,
        marker_color=BOROUGH_COLORS[borough],
        hovertemplate=f"Borough: {borough}<br>Range: $%{{x:.2f}}<br>Count: %{{y}}<extra></extra>"
    ))

fig_hist_detailed.update_layout(
    title="Detailed Distribution of Cost per Linear Foot by Borough ($25 bins)",
    xaxis_title="Cost per Linear Foot ($)",
    yaxis_title="Number of BIDs",
    width=1500,
    height=800,
    bargap=0.1,
    barmode='stack',
    showlegend=True,
    legend=dict(
        title="Borough",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01
    )
)

fig_hist_detailed.update_xaxes(tickformat="$,.2f")
fig_hist_detailed.show()

# Save histograms
fig_hist_detailed.write_html("plots/cost_per_foot_detailed.html")

# Print summary statistics for Cost per Linear Foot
print("\nSummary Statistics for Cost per Linear Foot:")
print(bid_data['Expense_per_linear_foot'].describe().round(2).to_string())

# Calculate financial percentages
financial_percentages = pd.DataFrame()
financial_percentages['BID Name:'] = bid_data['BID Name:']
financial_percentages['Borough'] = bid_data['Borough']  # Add borough information
financial_percentages['Total_Financial'] = bid_data['Total_Financial']
for column in FINANCIAL_COLUMNS:
    financial_percentages[f'{column} %'] = (bid_data[column] / bid_data['Total_Financial']) * 100
financial_percentages = financial_percentages.round(3)

# Sort and prepare labels for visualization
sorted_financial = financial_percentages.sort_values('Total_Financial', ascending=False)

# Create cumulative bar chart
fig_cumulative_all = go.Figure()

# Create a consistent color scheme for expense categories
EXPENSE_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                 '#aec7e8', '#ffbb78']

# Create the stacked bars
for i, column in enumerate(FINANCIAL_COLUMNS):
    fig_cumulative_all.add_trace(go.Bar(
        x=sorted_financial['BID Name:'],
        y=sorted_financial[f'{column} %'],
        name=column,
        marker=dict(color=EXPENSE_COLORS[i]),  # Use consistent colors for expense categories
        hovertemplate=f"<b>%{{x}}</b><br>{column}: %{{y:.2f}}%<br><extra></extra>"
    ))

# Create x-axis labels with budget information
x_labels = [f"{row['BID Name:']} (${int(row['Total_Financial']/1e6)}M)" if row['Total_Financial'] >= 1e6 
           else f"{row['BID Name:']} (${int(row['Total_Financial']/1e3)}K)" 
           for _, row in sorted_financial.iterrows()]

# Update layout with hidden default labels
fig_cumulative_all.update_layout(
    barmode='stack',
    xaxis_title="BID Name",
    yaxis_title="Percentage of Total Expenses",
    title="Distribution of Expenses Across All BIDs",
    width=2000,
    height=1200,
    showlegend=True,
    legend=dict(yanchor="top", y=1, xanchor="left", x=1.05),
    xaxis=dict(
        ticktext=x_labels,
        tickvals=sorted_financial['BID Name:'],
        showticklabels=False  # Hide default labels
    ),
    margin=dict(b=250),  # Keep large margin for labels
    yaxis=dict(
        range=[-25, 100]  # Extend y-axis range to show labels below 0
    )
)

# Add colored borough labels using annotations
for i, (_, row) in enumerate(sorted_financial.iterrows()):
    fig_cumulative_all.add_annotation(
        x=row['BID Name:'],
        y=0,  # Start at y=0 (bottom of bars)
        text=x_labels[i],
        showarrow=False,
        font=dict(
            size=12.5,
            family="Arial",
            color=BOROUGH_COLORS[row['Borough']]
        ),
        textangle=90,
        xanchor='center',
        yanchor='top'  # Align to top so text extends downward
    )

fig_cumulative_all.show()

# Save histograms
fig_cumulative_all.write_html("plots/expense_distribution.html")

# Calculate the mean of all the percentage columns in financial_percentages
avg_percentages = pd.Series({
    f'{col} %': financial_percentages[f'{col} %'].sum() / len(financial_percentages) 
    for col in FINANCIAL_COLUMNS
})

# Calculate dollar weighted average percentages for all BIDs
total_expenses_by_category = bid_data[FINANCIAL_COLUMNS].sum()
weighted_percentages = (total_expenses_by_category / total_expenses_by_category.sum()) * 100

# Get top 5 and bottom 25 BIDs by total financial
top_5_bids = bid_data.nlargest(5, 'Total_Financial')
bottom_25_bids = bid_data.nsmallest(25, 'Total_Financial')

# Calculate weighted averages for top 5
top_5_expenses = top_5_bids[FINANCIAL_COLUMNS].sum()
top_5_weighted = (top_5_expenses / top_5_expenses.sum()) * 100

# Calculate weighted averages for bottom 25
bottom_25_expenses = bottom_25_bids[FINANCIAL_COLUMNS].sum()
bottom_25_weighted = (bottom_25_expenses / bottom_25_expenses.sum()) * 100

# Create a stacked bar chart comparing all averages
fig_averages = go.Figure()

# Add bars for each expense category across all average types
for i, column in enumerate(FINANCIAL_COLUMNS):
    fig_averages.add_trace(go.Bar(
        x=['Simple Average (All BIDs)', 'Dollar Weighted Average (All BIDs)', 
           'Dollar Weighted Average (Top 5)', 'Dollar Weighted Average (Bottom 25)'],
        y=[avg_percentages[f'{column} %'], weighted_percentages[i], 
           top_5_weighted[i], bottom_25_weighted[i]],
        name=column,
        marker=dict(color=EXPENSE_COLORS[i]),  # Use consistent colors for expense categories
        hovertemplate=f"<b>{column}</b><br>%{{y:.2f}}%<br><extra></extra>"
    ))

# Update layout for the averages comparison chart
fig_averages.update_layout(
    barmode='stack',
    xaxis_title="Average Type",
    yaxis_title="Percentage",
    title="Comparison of Average Expense Distributions",
    width=2000,
    height=1200,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.05
    )
)

# Show the averages comparison chart
fig_averages.show()

# Save histograms
fig_averages.write_html("plots/expense_averages.html")

# Create histogram with 100k bins
fig_hist_100k = go.Figure()

# Add traces for each borough with 100k bins
for borough in BOROUGH_COLORS:
    borough_data = bid_data[bid_data['Borough'] == borough]
    fig_hist_100k.add_trace(go.Histogram(
        x=borough_data['Total_Financial'],
        xbins=dict(
            start=0,
            end=5200000,
            size=100000
        ),
        name=borough,
        marker_color=BOROUGH_COLORS[borough],
        hovertemplate=f"Borough: {borough}<br>Range: $%{{x:,.0f}}<br>Count: %{{y}}<extra></extra>"
    ))

fig_hist_100k.update_layout(
    title="Distribution of BID Total Expenses by Borough (100k bins)",
    xaxis_title="Total Expenses ($)",
    yaxis_title="Number of BIDs",
    width=1500,
    height=800,
    bargap=0.1,
    barmode='stack',
    showlegend=True,
    legend=dict(
        title="Borough",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01
    )
)

fig_hist_100k.update_xaxes(tickformat="$,.0f")
fig_hist_100k.show()

# Save histograms
fig_hist_100k.write_html("plots/total_expenses_100k.html")

# Create histogram with 1M bins
max_value = bid_data['Total_Financial'].max()
fig_hist_1m = go.Figure()

# Add traces for each borough with 1M bins
for borough in BOROUGH_COLORS:
    borough_data = bid_data[bid_data['Borough'] == borough]
    fig_hist_1m.add_trace(go.Histogram(
        x=borough_data['Total_Financial'],
        xbins=dict(
            start=0,
            end=max_value,
            size=1000000
        ),
        name=borough,
        marker_color=BOROUGH_COLORS[borough],
        hovertemplate=f"Borough: {borough}<br>Range: $%{{x:,.0f}}<br>Count: %{{y}}<extra></extra>"
    ))

fig_hist_1m.update_layout(
    title="Distribution of BID Total Expenses by Borough (1M bins)",
    xaxis_title="Total Expenses ($)",
    yaxis_title="Number of BIDs",
    width=1500,
    height=800,
    bargap=0.1,
    barmode='stack',
    showlegend=True,
    legend=dict(
        title="Borough",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.01
    )
)

fig_hist_1m.update_xaxes(tickformat="$,.0f")
fig_hist_1m.show()

# Save histograms
fig_hist_1m.write_html("plots/total_expenses_1m.html")

print("\nPlots have been saved to the 'plots' directory.")






