from flask import Flask, render_template_string
import pandas as pd
import imaplib
import email
import os
from datetime import datetime, timedelta

# ---------- Email Extraction Function ---------- #

def extract_emails():
    IMAP_SERVER = 'imap.example.com'  # Replace with actual server
    EMAIL_ACCOUNT = 'your_email@example.com'
    PASSWORD = 'your_password'

    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, PASSWORD)
        mail.select('inbox')

        # Fetch only recent emails (Last 7 Days)
        date_since = (datetime.utcnow() - timedelta(days=7)).strftime('%d-%b-%Y')
        status, data = mail.search(None, f'(SINCE {date_since})')
        
        email_ids = data[0].split()

        applications = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = msg['subject'] if msg['subject'] else "No Subject"
            from_ = msg['from'] if msg['from'] else "Unknown Sender"
            date_ = msg['date'] if msg['date'] else "Unknown Date"
            status = 'Pending'  # Default status

            try:
                parsed_date = email.utils.parsedate_to_datetime(date_)
            except Exception:
                parsed_date = datetime.utcnow()  # Fallback if date format is incorrect

            applications.append([subject, from_, parsed_date.strftime('%Y-%m-%d'), status])

        # Save to CSV (append new emails)
        df_new = pd.DataFrame(applications, columns=['Job Title', 'Company', 'Applied Date', 'Status'])

        # Load existing data (if any)
        if os.path.exists('applications.csv'):
            df_existing = pd.read_csv('applications.csv')
            df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['Job Title', 'Company', 'Applied Date'])
        else:
            df_combined = df_new

        df_combined.to_csv('applications.csv', index=False)

    except Exception as e:
        print(f"Error fetching emails: {e}")

# ---------- Flask Application ---------- #

app = Flask(__name__)

@app.route('/')
def display_table():
    extract_emails()  # Automatically fetch new emails before displaying

    # Load and sort the CSV file
    df = pd.read_csv('applications.csv')
    df['Applied Date'] = pd.to_datetime(df['Applied Date'], errors='coerce', utc=True)

    # Convert timestamps to timezone-naive
    df['Applied Date'] = df['Applied Date'].dt.tz_localize(None)

    # Filter and sort data
    df = df[df['Applied Date'] >= pd.Timestamp('2025-01-01')]
    df = df.sort_values(by='Applied Date', ascending=False)

    # Apply color formatting
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
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
