# old-gerbo.py
import requests
from bs4 import BeautifulSoup
import re
import json

# Create an empty list to store the results
results_list = []

# Define the API key and the custom search
api_key = "AIzaSyCchCL79RIvERFUp-jieQEhmV2U-ZDQXOo"
cse_id = "d567188f8b80949e9"

# Ask the user for the search term
search_term = input("Enter the search term: ")

# Replace spaces with underscores and remove special characters to create a valid filename
filename = re.sub('[^A-Za-z0-9]+', '_', search_term)

# Add the sites to exclude
search_term += " -site:reddit.com -site:wikipedia.org -site:.gov"

# Build the base API URL
base_url = "https://www.googleapis.com/customsearch/v1"

# Define the parameters for the request
params = {
    "key": api_key,
    "cx": cse_id,
    "q": search_term
}

# Make multiple requests to the API to get the first 100 results
for i in range(1, 101, 10):
    params['start'] = i
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx

        # Add the results to the list
        if response.status_code == 200:
            results = json.loads(response.text)
            for item in results['items']:
                results_list.append(item['link'])

    except requests.exceptions.HTTPError as err:
        if response.status_code == 429:
            print("Too many requests. Please input the list of websites manually.")
            results_list = input("Enter the websites separated by spaces: ").split()
            break
        else:
            print(f"HTTP error occurred: {err}")
            break

    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        print("Please input the list of websites manually.")
        results_list = input("Enter the websites separated by spaces: ").split()
        break

# Sort the list of results
sorted_results = sorted(results_list)

def find_contact_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find email addresses
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_regex, soup.text)

    # Find phone numbers
    phone_regex = r'\(?\b[0-9]{3}\)?[-.\s]?\b[0-9]{3}\b[-.\s]?\b[0-9]{4}\b'
    phones = re.findall(phone_regex, soup.text)

    # Add phone numbers from 'tel:' links
    for link in soup.find_all('a', href=True):
        if link['href'].startswith('tel:'):
            phone = link['href'].replace('tel:', '')
            phone = re.sub(r'%20', ' ', phone)  # Replace URL-encoded spaces
            phone = re.sub(r'\D', '', phone)  # Remove all non-digit characters
            phone = "+1 (" + phone[1:4] + ") " + phone[4:7] + "-" + phone[7:]  # Format the phone number
            phones.append(phone)

    # Format the phone numbers found by the regex
    for i in range(len(phones)):
        phone = phones[i]
        phone = re.sub(r'\D', '', phone)  # Remove all non-digit characters
        if len(phone) == 10:
            phone = "+1 (" + phone[:3] + ") " + phone[3:6] + "-" + phone[6:]  # Format the phone number
        phones[i] = phone

    # Remove duplicates
    phones = list(set(phones))

    return emails, phones

# Open the output file
with open(filename + '.txt', 'w') as f:
    # For each URL, prepend 'https://www.' if it's not already present, call the find_contact_info function and write the results to the file
    for url in sorted_results:
        if not url.startswith('http'):
            url = 'https://www.' + url
        emails, phones = find_contact_info(url)
        result = 'Website: ' + url + '\n' + 'Emails: ' + ', '.join(emails) + '\n' + 'Phones: ' + ', '.join(phones) + '\n' + '-------------------------\n'
        print(result)
        f.write(result)