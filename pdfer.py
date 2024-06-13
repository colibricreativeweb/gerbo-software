# pdfer.py
from flask import Flask, render_template, request, redirect, url_for
import PyPDF2
import re

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('upload_pdf.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
        emails = extract_emails(uploaded_file.filename)
        # Format the results
        formatted_emails = [f"{name}, {email}" for name, email in emails]
        return render_template('result.html', emails=formatted_emails)
    return redirect(url_for('home'))

def extract_emails(filename):
    pdf_file_obj = open(filename, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
    num_pages = pdf_reader.numPages
    email_list = []
    for i in range(num_pages):
        page_obj = pdf_reader.getPage(i)
        try:
            text = page_obj.extract_text()  # Updated method
        except KeyError:
            print(f"No text content in page {i}")
            continue
        # Updated regex to capture preceding text
        matches = re.findall(r"([a-zA-Z\s]+ \/ [a-zA-Z\s]+ \/ [a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+)", text, re.I)
        for match in matches:
            parts = match.split(' / ')
            if len(parts) == 3:
                name, title, email = parts
                # Remove unwanted characters from name and email
                name = name.replace('\n', '').strip()
                email = email.replace('\n', '').strip()
                email_list.append((name, email))
            else:
                email = parts[-1].replace('\n', '').strip()
                email_list.append(("-", email))  # Use "-" as placeholder if no name is found
    pdf_file_obj.close()
    return email_list

if __name__ == '__main__':
    app.run(debug=True)