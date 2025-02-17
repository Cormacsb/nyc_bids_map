import pandas as pd
import geopandas as gpd
import folium
from branca.colormap import LinearColormap
import shapely.wkt
from fuzzywuzzy import fuzz
import re

# Read the BIDs data and FY20 data
print("Reading data files...")
bids_data = pd.read_csv('BIDs/NYC_BIDS_09112015_20250113.csv')
fy20_data = pd.read_csv('BIDs/FY20_BID_Trends_Report_Data_20250110.csv')

def clean_bid_name(name):
    # Remove common variations and standardize
    name = str(name).lower()
    name = re.sub(r'\s+bid\b', '', name)  # Remove ' BID' at the end
    name = re.sub(r'\bdistrict\b', '', name)  # Remove 'district'
    name = re.sub(r'\b(business improvement|improvement)\b', '', name)  # Remove 'business improvement' or 'improvement'
    name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    return name.strip()

# Create a mapping of cleaned BID names to their original names and expenses
print("Creating BID name mappings...")
expense_lookup = {}
fy20_cleaned_names = {clean_bid_name(name): (name, expense) for name, expense in zip(fy20_data['BID Name:'], fy20_data['Total expenses'])}

# Get Church Avenue and Flatbush Avenue expenses for combined value
church_ave_expense = fy20_data[fy20_data['BID Name:'] == 'Church Avenue']['Total expenses'].iloc[0]
flatbush_ave_expense = fy20_data[fy20_data['BID Name:'] == 'Flatbush Avenue']['Total expenses'].iloc[0]
combined_expense = church_ave_expense + flatbush_ave_expense

# Manual overrides for specific matches
manual_matches = {
    'Alliance for Downtown New York': 'Downtown Alliance',
    'Myrtle Avenue': 'Myrtle Avenue (Queens)',
    'Myrtle Avenue Brooklyn Partnership': 'Myrtle Avenue (Brooklyn)',
    'Lower East Side': 'Lower East Side Partnership',
    'SoHo Broadway': 'SoHo Broadway Initiative',
    'Fulton Area Business (FAB) Alliance': 'FAB Fulton',
}

# Special cases where we need to handle the expense differently
special_expenses = {
    'Church Flatbush Community Alliance': combined_expense
}

def find_best_match(bid_name, threshold=60, return_details=False):
    # Check special data cases first
    if bid_name in special_data:
        if return_details:
            return special_data[bid_name], 100, "Combined Church Ave & Flatbush Ave"
        return special_data[bid_name]['expenses']
    
    # Check manual matches
    if bid_name in manual_matches:
        matched_name = manual_matches[bid_name]
        if matched_name in fy20_data_dict:
            if return_details:
                return fy20_data_dict[matched_name], 100, matched_name
            return fy20_data_dict[matched_name]['expenses']

    cleaned_name = clean_bid_name(bid_name)
    
    # Normal matching logic
    if cleaned_name in fy20_cleaned_names:
        matched_name = fy20_cleaned_names[cleaned_name][0]
        if return_details:
            return fy20_data_dict[matched_name], 100, matched_name
        return fy20_data_dict[matched_name]['expenses']
    
    # If no exact match, try fuzzy matching
    best_ratio = 0
    best_match = None
    best_original = None
    
    for clean_name, (original_name, _) in fy20_cleaned_names.items():
        # Skip the incorrect West Village -> Bayside Village match
        if bid_name == 'West Village' and original_name == 'Bayside Village':
            continue
            
        ratio = fuzz.ratio(cleaned_name, clean_name)
        if ratio > best_ratio and ratio > threshold:
            best_ratio = ratio
            best_match = fy20_data_dict[original_name]
            best_original = original_name
    
    if return_details:
        return best_match, best_ratio, best_original
    return best_match['expenses'] if best_match else None

# Convert WKT strings to shapely geometries
print("Converting geometries...")
bids_data['geometry'] = bids_data['the_geom'].apply(shapely.wkt.loads)

# Convert to GeoDataFrame with correct CRS
bids_gdf = gpd.GeoDataFrame(bids_data, geometry='geometry', crs="EPSG:4326")

# Create a base map centered on NYC
print("Creating map...")
nyc_map = folium.Map(
    location=[40.7128, -74.0060],
    zoom_start=11,
    tiles='CartoDB positron'
)

# Create a color map based on founding years with red-orange-yellow-green-blue transitions
years = bids_gdf['Year_Found'].astype(float)
print(f"\nYear range: {years.min()} to {years.max()}")

colormap = LinearColormap(
    colors=[
        # Reds (10 shades)
        '#67000d', '#800000', '#990000', '#b30000', '#cc0000', '#e60000', '#ff0000', '#ff1a1a', '#ff3333', '#ff4d4d',
        
        # Red-Orange transition (10 shades)
        '#ff6600', '#ff751a', '#ff8533', '#ff944d', '#ffa366', '#ffb380', '#ffc299', '#ffd1b3', '#ffe0cc', '#fff0e6',
        
        # Yellows (10 shades)
        '#ffff00', '#ffff1a', '#ffff33', '#ffff4d', '#ffff66', '#ffff80', '#ffff99', '#ffffb3', '#ffffcc', '#ffffe6',
        
        # Yellow-Green transition (10 shades)
        '#e6ff00', '#ccff00', '#b3ff00', '#99ff00', '#80ff00', '#66ff00', '#4dff00', '#33ff00', '#1aff00', '#00ff00',
        
        # Green-Blue transition (10 shades)
        '#00e600', '#00cc00', '#00b300', '#009900', '#008000', '#006600', '#004d00', '#003300', '#000066', '#000099'
    ],
    vmin=years.min(),
    vmax=years.max()
)

# Add the colormap to the map
colormap.add_to(nyc_map)
colormap.caption = 'Year Founded'

# Track matching statistics and unmatched BIDs
total_bids = 0
matched_bids = 0
unmatched_bids = []

# Create a mapping of BID names to their FY20 data
fy20_data_dict = {}
for _, row in fy20_data.iterrows():
    bid_name = row['BID Name:']
    # Convert numeric fields, handling NaN values
    full_time = pd.to_numeric(row['Full-time staff'], errors='coerce', downcast='integer')
    sanitation = pd.to_numeric(row['Sanitation staff employed'], errors='coerce', downcast='integer')
    safety = pd.to_numeric(row['Public Safety staff employed'], errors='coerce', downcast='integer')
    
    full_time_total = 0
    if pd.notna(full_time): full_time_total += full_time
    if pd.notna(sanitation): full_time_total += sanitation
    if pd.notna(safety): full_time_total += safety
    
    fy20_data_dict[bid_name] = {
        'expenses': row['Total expenses'],
        'full_time_total': full_time_total if full_time_total > 0 else None,
        'trash_bags': pd.to_numeric(row['Trash bags collected'], errors='coerce', downcast='integer'),
        'receptacles': pd.to_numeric(row['Trash and recycling receptacles serviced'], errors='coerce', downcast='integer'),
        'safety_interactions': pd.to_numeric(row['Interactions with public safety officers'], errors='coerce', downcast='integer'),
        'art_installations': pd.to_numeric(row['Public art installations sponsored'], errors='coerce', downcast='integer')
    }

# Get Church Avenue and Flatbush Avenue data for combined values
church_ave_data = fy20_data[fy20_data['BID Name:'] == 'Church Avenue'].iloc[0]
flatbush_ave_data = fy20_data[fy20_data['BID Name:'] == 'Flatbush Avenue'].iloc[0]

# Function to safely add numeric values
def safe_add(val1, val2):
    if pd.isna(val1) and pd.isna(val2):
        return None
    elif pd.isna(val1):
        return val2
    elif pd.isna(val2):
        return val1
    return val1 + val2

# Combine the data
combined_data = {
    'expenses': church_ave_expense + flatbush_ave_expense,
    'full_time_total': safe_add(
        fy20_data_dict['Church Avenue']['full_time_total'],
        fy20_data_dict['Flatbush Avenue']['full_time_total']
    ),
    'trash_bags': safe_add(
        fy20_data_dict['Church Avenue']['trash_bags'],
        fy20_data_dict['Flatbush Avenue']['trash_bags']
    ),
    'receptacles': safe_add(
        fy20_data_dict['Church Avenue']['receptacles'],
        fy20_data_dict['Flatbush Avenue']['receptacles']
    ),
    'safety_interactions': safe_add(
        fy20_data_dict['Church Avenue']['safety_interactions'],
        fy20_data_dict['Flatbush Avenue']['safety_interactions']
    ),
    'art_installations': safe_add(
        fy20_data_dict['Church Avenue']['art_installations'],
        fy20_data_dict['Flatbush Avenue']['art_installations']
    )
}

# Special cases where we need to handle the data differently
special_data = {
    'Church Flatbush Community Alliance': combined_data
}

def get_fy20_data(bid_name, return_details=False):
    # Check special data cases first
    if bid_name in special_data:
        if return_details:
            return special_data[bid_name]
        return special_data[bid_name]['expenses']
    
    # Check manual matches
    if bid_name in manual_matches:
        matched_name = manual_matches[bid_name]
        if matched_name in fy20_data_dict:
            if return_details:
                return fy20_data_dict[matched_name]
            return fy20_data_dict[matched_name]['expenses']

    cleaned_name = clean_bid_name(bid_name)
    
    # Normal matching logic
    if cleaned_name in fy20_cleaned_names:
        matched_name = fy20_cleaned_names[cleaned_name][0]
        if return_details:
            return fy20_data_dict[matched_name]
        return fy20_data_dict[matched_name]['expenses']
    
    # If no exact match, try fuzzy matching
    best_ratio = 0
    best_match = None
    
    for clean_name, (original_name, _) in fy20_cleaned_names.items():
        # Skip the incorrect West Village -> Bayside Village match
        if bid_name == 'West Village' and original_name == 'Bayside Village':
            continue
            
        ratio = fuzz.ratio(cleaned_name, clean_name)
        if ratio > best_ratio and ratio > 60:
            best_ratio = ratio
            best_match = original_name
    
    if best_match and best_match in fy20_data_dict:
        if return_details:
            return fy20_data_dict[best_match]
        return fy20_data_dict[best_match]['expenses']
    
    if return_details:
        return None
    return None

# Add BID boundaries to the map
print("\nAdding boundaries to map...")
for idx, row in bids_gdf.iterrows():
    try:
        total_bids += 1
        # Get the FY20 data for this BID
        bid_name = row['F_ALL_BI_2']
        fy20_data = get_fy20_data(bid_name, return_details=True)
        
        if fy20_data is not None:
            matched_bids += 1
            expense_str = f"${fy20_data['expenses']:,.2f}"
            
            # Format the additional data points - show 0 instead of 'Not available' when we have data
            full_time = fy20_data['full_time_total']
            full_time_str = f"{int(full_time):,}" if pd.notna(full_time) else '0'
            
            trash_bags = fy20_data['trash_bags']
            trash_bags_str = f"{int(trash_bags):,}" if pd.notna(trash_bags) else '0'
            
            receptacles = fy20_data['receptacles']
            receptacles_str = f"{int(receptacles):,}" if pd.notna(receptacles) else '0'
            
            safety = fy20_data['safety_interactions']
            safety_str = f"{int(safety):,}" if pd.notna(safety) else '0'
            
            art = fy20_data['art_installations']
            art_str = f"{int(art):,}" if pd.notna(art) else '0'
        else:
            # Keep 'Not available' only when we have no data at all for the BID
            expense_str = 'Not available'
            full_time_str = 'Not available'
            trash_bags_str = 'Not available'
            receptacles_str = 'Not available'
            safety_str = 'Not available'
            art_str = 'Not available'
        
        # Create a tooltip with BID info
        tooltip = f"""
        <b>{bid_name}</b><br>
        Founded: {int(row['Year_Found'])}<br>
        <br>
        <b>FY20 Data:</b><br>
        Total Expenses: {expense_str}<br>
        Full-time Staff: {full_time_str}<br>
        Trash Bags Collected: {trash_bags_str}<br>
        Receptacles Serviced: {receptacles_str}<br>
        Public Safety Interactions: {safety_str}<br>
        Public Art Installations: {art_str}
        """
        
        # Add the polygon to the map
        folium.GeoJson(
            row['geometry'].__geo_interface__,
            style_function=lambda x, year=row['Year_Found']: {
                'fillColor': colormap(year),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7
            },
            tooltip=tooltip
        ).add_to(nyc_map)
    except Exception as e:
        print(f"Error adding BID {bid_name}: {str(e)}")

print(f"\nMatched {matched_bids} out of {total_bids} BIDs with expense data")

# Get all unmatched BIDs from both datasets
matched_bids_names = set()
for bid_name in bids_data['F_ALL_BI_2']:
    if get_fy20_data(bid_name) is not None:
        matched_bids_names.add(bid_name)

matched_fy20_names = set()
for bid_name in fy20_data_dict.keys():
    # Check if this FY20 BID name is used in any match
    is_matched = False
    # Check manual matches
    for orig_name, match_name in manual_matches.items():
        if bid_name == match_name:
            is_matched = True
            break
    # Check fuzzy matches
    if not is_matched:
        for orig_name in bids_data['F_ALL_BI_2']:
            fy20_data = get_fy20_data(orig_name, return_details=True)
            if fy20_data is not None and bid_name in fy20_data_dict:
                is_matched = True
                break
    if is_matched:
        matched_fy20_names.add(bid_name)

unmatched_bids = set(bids_data['F_ALL_BI_2']) - matched_bids_names
unmatched_fy20 = set(fy20_data_dict.keys()) - matched_fy20_names

print("\n=== MATCHING SUMMARY ===")
print(f"\nFrom the original BIDs dataset ({len(bids_data)} total BIDs):")
print(f"Successfully matched: {matched_bids} BIDs")
print(f"Unmatched: {total_bids - matched_bids} BIDs")
print("\nThe unmatched BIDs are:")
unmatched_original = []
for bid_name in bids_data['F_ALL_BI_2']:
    if get_fy20_data(bid_name) is None:
        unmatched_original.append(bid_name)
for name in sorted(unmatched_original):
    print(f"  - {name}")

print(f"\nFrom the FY20 dataset ({len(fy20_data_dict)} total BIDs):")
print(f"Successfully matched: {len(matched_fy20_names)} BIDs")
print(f"Unmatched: {len(unmatched_fy20)} BIDs")
print("\nThe unmatched FY20 BIDs are:")
for name in sorted(unmatched_fy20):
    print(f"  - {name}")

print("\nSaving map...")
nyc_map.save('BIDs/nyc_bids_map.html')
print("Done!")


