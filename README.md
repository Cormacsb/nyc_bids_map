# NYC Business Improvement Districts Analysis

This repository contains interactive visualizations of New York City's Business Improvement Districts (BIDs) data, including:

1. An interactive map showing BIDs color-coded by founding year
2. A series of interactive plots analyzing FY2020 operational data

## Interactive Map

The map shows all 76 NYC BIDs with:
* Color gradient showing founding years (1976-2023)
* Hover information showing detailed FY2020 operational data
* Interactive zoom and pan controls

Embed the map using:
```html
<iframe 
    src="https://cormacsb.github.io/nyc_bids_map/"
    width="100%" 
    height="600" 
    frameborder="0">
</iframe>
```

## Interactive Plots

The analysis includes several interactive plots:
* BID Total Expenses vs Cost per Linear Foot (by borough)
* Distribution of Cost per Linear Foot
* Detailed expense breakdowns
* Comparative analyses

View all plots at: [https://cormacsb.github.io/nyc_bids_map/plots/](https://cormacsb.github.io/nyc_bids_map/plots/)

Embed any plot using:
```html
<iframe 
    src="https://cormacsb.github.io/nyc_bids_map/plots/[plot-name].html"
    width="100%" 
    height="800" 
    frameborder="0"
    scrolling="no">
</iframe>
```

Replace [plot-name] with one of:
* bid_expenses_vs_linear_foot
* cost_per_foot_distribution
* cost_per_foot_detailed
* expense_distribution
* expense_averages
* total_expenses_100k
* total_expenses_1m

## Data Sources

* NYC BIDs geographical and founding year data
* FY2020 BID Trends Report Data 