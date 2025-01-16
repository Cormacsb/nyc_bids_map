import os
import re

RESPONSIVE_HEADER = '''<!DOCTYPE html>
<html>
<head>
    <title>NYC BIDs Plot</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        #plotly-div {
            width: 100vw;
            height: 100vh;
        }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="plotly-div">'''

RESPONSIVE_FOOTER = '''    </div>
</body>
</html>'''

def update_plot_file(filename):
    if not filename.endswith('.html') or filename in ['index.html', 'template.html']:
        return
        
    filepath = os.path.join('plots', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the plot data and script
    plot_match = re.search(r'<div id="[^"]*">(.*?)</div>\s*<script>', content, re.DOTALL)
    script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
    
    if plot_match and script_match:
        plot_data = plot_match.group(1)
        script_content = script_match.group(1)
        
        # Create new responsive version
        new_content = f"{RESPONSIVE_HEADER}\n{plot_data}\n    <script>\n{script_content}\n    </script>\n{RESPONSIVE_FOOTER}"
        
        # Write to temp file first
        temp_filepath = os.path.join('plots', 'temp', filename)
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Replace original with temp file
        os.replace(temp_filepath, filepath)

def main():
    # Update all plot files
    for filename in os.listdir('plots'):
        update_plot_file(filename)

if __name__ == '__main__':
    main() 