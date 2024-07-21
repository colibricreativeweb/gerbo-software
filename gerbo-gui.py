# gerbo-gui.py
from flask import Flask, request, render_template, flash, redirect, url_for, session, jsonify
from datetime import datetime
import requests
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import pandas as pd
import os
import subprocess
import numpy as np
import PyPDF2
from pdfminer.high_level import extract_text
import re

load_dotenv()  # load environment variables

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # replace with your secret key
app.config['UPLOAD_FOLDER'] = 'excels'  # replace with your upload folder

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        filenames = []
        cols = set()  # change this to a set
        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenames.append(filename)
                df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # read the entire file

                # Normalize column names to have the first letter uppercase and the rest lowercase
                df.columns = df.columns.str.capitalize()

                # Combine duplicate columns
                df = df.groupby(df.columns, axis=1).sum()

                # Ignore if the redundant cols are empty
                df = df.loc[:, (df != '').any(axis=0)]

                # Check if there are still any duplicate or empty columns
                if df.columns.duplicated().any():
                    print(f"Warning: There are still duplicate columns in {filename}")
                if df.isnull().all().any():
                    print(f"Warning: There are still empty columns in {filename}")

                # Save the modified DataFrame back to the original file
                df.to_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename), index=False)

                cols.update(df.columns.tolist())  # use the update method to add the columns to the set
        session['cols'] = list(cols)  # convert the set back to a list before storing it in the session
        return redirect(url_for('search_files', filenames=','.join(filenames)))
    return render_template('upload.html')

def extract_emails(filename):
    email_list = []
    # Start with PyPDF2 for basic extraction
    try:
        pdf_file_obj = open(filename, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
        text = ''
        for i in range(pdf_reader.numPages):
            page_obj = pdf_reader.getPage(i)
            text += page_obj.extract_text()
        if not text:
            raise ValueError("No text extracted with PyPDF2; trying PDFMiner.")
        print("Text extracted with PyPDF2.")
    except Exception as e:
        print(e)
        # Fallback to PDFMiner for complex PDFs
        text = extract_text(filename)
        print("Text extracted with PDFMiner.")

    # Use regex to find all emails in the text
    email_matches = re.findall(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
    for email in set(email_matches):  # Use set to remove duplicates
        email = email.replace('\n', '').strip()
        email_list.append({'email': email})

    if pdf_file_obj:
        pdf_file_obj.close()
    return email_list

@app.route('/upload_pdf', methods=['GET', 'POST'])
def upload_pdf():
    if request.method == 'POST':
        files = request.files.getlist('file')  # Get list of files
        if not files or files[0].filename == '':
            flash('No selected files')
            return redirect(request.url)
        
        all_emails = []  # List to hold emails from all PDFs
        pdf_folder = 'pdfs'
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
        
        for file in files:
            if file:  # Check if file exists
                filename = secure_filename(file.filename)
                file_path = os.path.join(pdf_folder, filename)
                file.save(file_path)
                emails = extract_emails(file_path)
                all_emails.extend(emails)  # Add emails from current PDF to the list
        
        email_count = len(all_emails)
        return render_template('pdf_results.html', emails=all_emails, email_count=email_count)
    # If it's a GET request or the POST request was not successful, render the upload form
    return render_template('upload_pdf.html')

@app.route('/search', methods=['GET', 'POST'])
def search_files():
    try:
        if request.method == 'POST':
            search_terms = request.form.get('search_term').replace('\r\n', '\n').split('\n')  # split the search term by line breaks
            selected_cols = request.form.getlist('cols')  # get the selected columns
            filenames = request.args.get('filenames', '').split(',')
            filenames = [f for f in filenames if f]  # remove empty strings
            if not filenames:
                flash('No files uploaded')
                return redirect(url_for('upload_files'))

            # Get the checkbox value from the form data
            exclude_words_checkbox = request.form.get('toggle')

            # Get the exclude words from the form data if the checkbox is checked
            exclude_words = request.form.get('exclude_words', '').replace('\r\n', '\n').split('\n') if exclude_words_checkbox else []

            # Get the custom name checkbox value from the form data
            custom_name_checkbox = request.form.get('customNameToggle')

            # Get the custom name from the form data if the checkbox is checked
            custom_name = request.form.get('custom_name', '') if custom_name_checkbox else None

            results = pd.DataFrame()
            for filename in filenames:
                try:
                    df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    if selected_cols:  # if any columns were selected
                        missing_cols = [col for col in selected_cols if col not in df.columns]
                        if missing_cols:
                            flash(f'Columns {", ".join(missing_cols)} not found in file {filename}.')
                            continue
                        df = df[selected_cols]  # select only the selected columns
                    for term in search_terms:  # loop over each search term
                        if term == "$all":
                            results = pd.concat([results, df])
                        else:
                            results = pd.concat([results, df[df.apply(lambda row: row.astype(str).str.contains(term, case=False).any(), axis=1)]])
                    # If the exclude words field is not empty, remove the rows that contain any of the exclude words
                    if exclude_words:
                        for word in exclude_words:
                            results = results[~results.apply(lambda row: row.astype(str).str.contains(word, case=False).any(), axis=1)]
                except Exception as e:
                    flash(f'Error processing file {filename}: {str(e)}')
                    continue

            # Get the current date and time
            now = datetime.now()

            # Format the current date and time as a string
            now_str = now.strftime('%Y%m%d%H%M%S')

            # Use the custom name if provided, else use the current date and time as the Excel file name
            excel_file_name = os.path.join('databases', f'{custom_name if custom_name else "search_results_" + now_str}.xlsx')

            results.to_excel(excel_file_name, index=False)  # save the results to an Excel file

            try:
                # run database.py after the search results are generated
                subprocess.run(['python', 'database.py', excel_file_name, custom_name if custom_name else ''], check=True)
            except Exception as e:
                flash(f'Error running database script: {str(e)}')

            return render_template('ex_results.html', results=results.to_html(classes='min-w-full divide-y divide-gray-200'))
        
        # Sort the columns before passing them to the template
        sorted_cols = sorted(session.get('cols', []))
        return render_template('search.html', cols=sorted_cols)  # pass the sorted column names to the search page
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        exclude_sites = request.form.get('exclude_sites')

        # Get the extra parameters from the form data
        language = request.form.get('language')
        """ fileType = request.form.get('fileType') """
        country = request.form.get('country')

        # Store the original search term for display
        display_search_term = search_term

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

        return render_template('results.html', contact_info=contact_info, year=datetime.now().year, search_term=display_search_term)

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