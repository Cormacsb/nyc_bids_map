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

def create_responsive_layout(fig, title, xaxis_title, yaxis_title):
    """Helper function to create responsive layouts"""
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=100),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        ),
        template="plotly_white"
    )

def save_responsive_plot(fig, filename):
    """Helper function to save plots with responsive template"""
    with open('plots/template.html', 'r') as template_file:
        template = template_file.read()
    
    plot_html = fig.to_html(full_html=False, include_plotlyjs=False)
    final_html = template.replace('<!-- Plot will be inserted here -->', plot_html)
    
    with open(f'plots/{filename}', 'w') as f:
        f.write(final_html)

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

create_responsive_layout(
    fig_scatter,
    "BID Total Expenses vs Cost per Linear Foot by Borough (Log Scale)",
    "Total Expenses ($)",
    "Cost per Linear Foot ($)"
)

fig_scatter.update_layout(
    xaxis_type="log",
    yaxis_type="log",
    xaxis=dict(
        type="log",
        tickformat="$,.0f",
        tickvals=[1e5, 2e5, 4e5, 7e5, 1e6, 2e6, 4e6, 7e6, 1e7, 2e7],
        tickangle=45,
        tickfont=dict(size=10)
    )
)

fig_scatter.update_yaxes(tickformat="$,.2f")
save_responsive_plot(fig_scatter, "bid_expenses_vs_linear_foot.html")

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

create_responsive_layout(
    fig_hist_linear,
    "Distribution of Cost per Linear Foot by Borough",
    "Cost per Linear Foot ($)",
    "Number of BIDs"
)

fig_hist_linear.update_layout(
    bargap=0.1,
    barmode='stack'
)

fig_hist_linear.update_xaxes(tickformat="$,.2f")
save_responsive_plot(fig_hist_linear, "cost_per_foot_distribution.html")

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

create_responsive_layout(
    fig_hist_detailed,
    "Detailed Distribution of Cost per Linear Foot by Borough ($25 bins)",
    "Cost per Linear Foot ($)",
    "Number of BIDs"
)

fig_hist_detailed.update_layout(
    bargap=0.1,
    barmode='stack'
)

fig_hist_detailed.update_xaxes(tickformat="$,.2f")
save_responsive_plot(fig_hist_detailed, "cost_per_foot_detailed.html")

# Calculate financial percentages
financial_percentages = pd.DataFrame()
financial_percentages['BID Name:'] = bid_data['BID Name:']
financial_percentages['Borough'] = bid_data['Borough']
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
        marker=dict(color=EXPENSE_COLORS[i]),
        hovertemplate=f"<b>%{{x}}</b><br>{column}: %{{y:.2f}}%<br><extra></extra>"
    ))

# Create x-axis labels with budget information
x_labels = [f"{row['BID Name:']} (${int(row['Total_Financial']/1e6)}M)" if row['Total_Financial'] >= 1e6 
           else f"{row['BID Name:']} (${int(row['Total_Financial']/1e3)}K)" 
           for _, row in sorted_financial.iterrows()]

create_responsive_layout(
    fig_cumulative_all,
    "Distribution of Expenses Across All BIDs",
    "BID Name",
    "Percentage of Total Expenses"
)

fig_cumulative_all.update_layout(
    barmode='stack',
    xaxis=dict(
        ticktext=x_labels,
        tickvals=sorted_financial['BID Name:'],
        tickangle=45,
        showticklabels=True
    ),
    yaxis=dict(range=[0, 100])
)

save_responsive_plot(fig_cumulative_all, "expense_distribution.html")

print("All plots have been generated with responsive design!")






