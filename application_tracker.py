from flask import Flask, render_template_string
import pandas as pd
import imaplib
import email
from datetime import datetime

# ---------- Email Extraction Section ---------- #

def extract_emails():
    # Replace with your actual email credentials and server details
    IMAP_SERVER = 'imap.example.com'
    EMAIL_ACCOUNT = 'your_email@example.com'
    PASSWORD = 'your_password'

    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select('inbox')

    # Search for all emails
    status, data = mail.search(None, 'ALL')
    email_ids = data[0].split()

    applications = []
    for e_id in email_ids:
        status, msg_data = mail.fetch(e_id, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = msg['subject']
        from_ = msg['from']
        date_ = msg['date']
        status = 'Pending'  # Default status, can be updated later

        applications.append([subject, from_, date_, status])

    # Save to CSV
    df = pd.DataFrame(applications, columns=['Job Title', 'Company', 'Applied Date', 'Status'])
    df.to_csv('applications.csv', index=False)

# Uncomment to extract emails when needed
# extract_emails()

# ---------- Flask Application Section ---------- #

app = Flask(__name__)

@app.route('/')
def display_table():
    # Load and sort the CSV file
    df = pd.read_csv('applications.csv')
    df['Applied Date'] = pd.to_datetime(df['Applied Date'], errors='coerce')

    # Make timestamps timezone-naive
    df['Applied Date'] = df['Applied Date'].apply(lambda x: x.tz_convert(None) if pd.notnull(x) and x.tzinfo else x)

    # Filter and sort the data
    df = df[df['Applied Date'] >= pd.Timestamp('2025-01-01')]
    df = df.sort_values(by='Applied Date', ascending=False)

    # Generate HTML table
    def apply_color(status):
        return {
            'Pending': 'color: yellow;',
            'Sorry': 'color: red;',
            'Selected': 'color: green;'
        }.get(status, '')

    rows = "".join([
        f"<tr>"
        f"<td>{row['Job Title']}</td>"
        f"<td>{row['Company']}</td>"
        f"<td>{row['Applied Date'].strftime('%Y-%m-%d') if pd.notnull(row['Applied Date']) else ''}</td>"
        f"<td style='{apply_color(row['Status'])}'>{row['Status']}</td>"
        f"</tr>"
        for _, row in df.iterrows()
    ])

    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Job Applications</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background-color: #f4f4f9;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                padding: 20px;
            }}

            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 20px;
            }}

            table {{
                background-color: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}

            th {{
                background-color: #4CAF50;
                color: white;
                text-align: center;
            }}

            td, th {{
                padding: 15px;
                text-align: left;
            }}

            tr:hover {{
                background-color: #f1f1f1;
            }}

            .status {{
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 5px;
            }}

            .Pending {{ color: yellow; }}
            .Sorry {{ color: red; }}
            .Selected {{ color: green; }}
        </style>
    </head>
    <body>
        <h1>📋 Job Applications Tracker</h1>
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>Job Title</th>
                    <th>Company Name</th>
                    <th>Applied Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
