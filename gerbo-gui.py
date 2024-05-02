# gerbo-gui.py
from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime
import requests
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import pandas as pd
import os

load_dotenv()  # load environment variables

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # replace with your secret key
app.config['UPLOAD_FOLDER'] = 'excels'  # replace with your upload folder

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('search_file',
                                    filename=filename))
    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search_file():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        filename = request.args.get('filename')
        df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        results = df[df.apply(lambda row: row.astype(str).str.contains(search_term).any(), axis=1)]
        return render_template('ex_results.html', results=results.to_html())
    return render_template('search.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        exclude_sites = request.form.get('exclude_sites')

        # Get the extra parameters from the form data
        language = request.form.get('language')
        """ fileType = request.form.get('fileType') """
        country = request.form.get('country')

        filename = re.sub('[^A-Za-z0-9]+', '_', search_term)

        search_term += " -site:reddit.com -site:wikipedia.org -site:.gov"
        if exclude_sites:
            for site in exclude_sites.split(' '):
                search_term += f" -site:{site.strip()}"

        base_url = "https://www.googleapis.com/customsearch/v1"

        params = {
            "key": os.getenv("GOOGLE_API_KEY"),  # replace with environment variable
            "cx": os.getenv("GOOGLE_CX_KEY"),  # replace with environment variable
            "q": search_term
        }

        # Add the extra parameters to the params dictionary if they are not None
        if language:
            params['lr'] = language
        """ if fileType:
            params['fileType'] = fileType """
        if country:
            params['gl'] = country
            
            # Print the parameters (DELETE AFTER USE)
        print(f"Sending the following parameters to the API: {params}")


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
                        flash("No se encontraron resultados.")
                        return redirect(url_for('index'))

            except requests.exceptions.HTTPError as err:
                if response.status_code == 429:
                    flash("Demasiadas solicitudes. Por favor ingrese los websites manualmente.")
                    return redirect(url_for('manual'))
                else:
                    flash(f"HTTP ocurrió un error: {err}")
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

    # Remove duplicate emails and phones
    emails = list(set(emails))
    phones = list(set(phones))

    return emails, phones

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use port 5000 if PORT isn't set
    app.run(host='0.0.0.0', port=port, debug=False)