import sys
import os
import requests
from bs4 import BeautifulSoup
'''
parse_lyme_minutes.py

This reads a file of HTML retrieved from the Lyme NH website
Usual URL is something like: https://www.lymenh.gov/node/101/minutes/2024
Save the entire HTML page into the LymeTownMinutes (as PB-2024.html)
Run this program, using `--file https://www.lymenh.gov/node/101/minutes/2024`
(the --url option doesn't work - gives a weird http error)
It produces a shell script that curl's the individual PDF minutes into the
LymeTownMinutes folder.

Thanks to ChatGPT for the help.
'''
def fetch_html_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)

def read_html_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

# Ensure at least one argument (URL or file path) is provided
if len(sys.argv) != 3 or sys.argv[1] not in ("--url", "--file"):
    print("Usage: python3 parse_to_script.py (--url <url> | --file <file_path>)")
    sys.exit(1)

source_type = sys.argv[1]
source = sys.argv[2]

# Get the HTML content
if source_type == "--url":
    html_content = fetch_html_from_url(source)
    output_file = "output.sh"  # Default output shell script file for URL case
else:  # source_type == "--file"
    html_content = read_html_from_file(source)
    output_file = f"{os.path.splitext(source)[0]}.sh"

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Find all divs with class 'contextual-links-region'
divs = soup.find_all('div', class_='contextual-links-region')

# Base URL
base_url = "https://www.lymenh.gov"

# Extract data and build curl commands
commands = []
for div in divs:
    # Extract the link and link text
    a_tag = div.find('a', href=True)
    if a_tag:
        url_path = a_tag['href']
        link_text = a_tag.text.strip().replace(' ', '_')  # Replace spaces in link text with underscores

        # Extract the date and format it
        date_span = div.find('span', class_='date-display-single')
        date_text = date_span.text.strip() if date_span else ''
        date_formatted = date_span['content'].split('T')[0] if date_span and 'content' in date_span.attrs else ''

        # Construct the output filename
        output_filename = f"{link_text}_{date_formatted}.pdf"

        # Construct the curl command with -L option
        full_url = f"{base_url}{url_path}"
        curl_command = f'curl -L -o "{output_filename}" "{full_url}"'
        commands.append(curl_command)

# Write to shell script file
with open(output_file, 'w', encoding='utf-8') as file:
    file.write("#!/bin/bash\n")
    file.write("# Created automatically by parse-lyme-minutes.py\n\n")
    file.write("\n".join(commands) + "\n")

print(f"Shell script written to {output_file}")
