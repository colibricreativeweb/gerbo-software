from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime
import requests
import json
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # replace with your secret key

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        exclude_sites = request.form.get('exclude_sites')

        filename = re.sub('[^A-Za-z0-9]+', '_', search_term)

        search_term += " -site:reddit.com -site:wikipedia.org -site:.gov"
        if exclude_sites:
            for site in exclude_sites.split(' '):
                search_term += f" -site:{site.strip()}"

        base_url = "https://www.googleapis.com/customsearch/v1"

        params = {
            "key": "AIzaSyCchCL79RIvERFUp-jieQEhmV2U-ZDQXOo",
            "cx": "d567188f8b80949e9",
            "q": search_term
        }

        results_list = []
        for i in range(1, 21, 10):
            params['start'] = i
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()

                if response.status_code == 200:
                    results = json.loads(response.text)
                    if 'items' in results:
                        for item in results['items']:
                            results_list.append(item['link'])
                    else:
                        flash("No results found.")
                        return redirect(url_for('index'))

            except requests.exceptions.HTTPError as err:
                if response.status_code == 429:
                    flash("Too many requests. Please enter the websites manually.")
                    return redirect(url_for('manual'))
                else:
                    flash(f"HTTP error occurred: {err}")
                    return redirect(url_for('index'))

        sorted_results = sorted(results_list)

        contact_info = []
        for url in sorted_results:
            emails, phones = find_contact_info(url)
            contact_info.append({
                'website': url,
                'emails': emails,
                'phones': phones
            })

        return render_template('results.html', contact_info=contact_info, year=datetime.now().year)

    return render_template('index.html', year=datetime.now().year)

@app.route('/manual', methods=['GET', 'POST'])
def manual():
    if request.method == 'POST':
        websites = request.form.get('websites')
        websites = websites.split(' ')

        contact_info = []
        for website in websites:
            website = website.strip()
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            emails, phones = find_contact_info(website)
            contact_info.append({
                'website': website,
                'emails': emails,
                'phones': phones
            })

        return render_template('results.html', contact_info=contact_info, year=datetime.now().year)

    return render_template('manual.html', year=datetime.now().year)

def find_contact_info(url):
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        return [], []  # return empty lists if a connection error occurs

    soup = BeautifulSoup(response.text, 'html.parser')

    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_regex, soup.text)

    phone_regex = r'\(?\b[0-9]{3}\)?[-.\s]?\b[0-9]{3}\b[-.\s]?\b[0-9]{4}\b'
    phones = re.findall(phone_regex, soup.text)

    for link in soup.find_all('a', href=True):
        if link['href'].startswith('tel:'):
            phone = link['href'].replace('tel:', '')
            phone = re.sub(r'%20', ' ', phone)
            phone = re.sub(r'\D', '', phone)
            phone = "+1 (" + phone[1:4] + ") " + phone[4:7] + "-" + phone[7:]
            phones.append(phone)

    for i in range(len(phones)):
        phone = phones[i]
        phone = re.sub(r'\D', '', phone)
        if len(phone) == 10:
            phone = "+1 (" + phone[:3] + ") " + phone[3:6] + "-" + phone[6:]
        phones[i] = phone

    phones = list(set(phones))

    return emails, phones

if __name__ == '__main__':
    app.run(debug=True)