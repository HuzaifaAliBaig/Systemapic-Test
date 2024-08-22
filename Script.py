import pdfplumber
import re
import requests
import json
from dotenv import load_dotenv

MONDAY_API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQwMDQxMjY4NywiYWFpIjoxMSwidWlkIjo2NTA5Mzk0MywiaWFkIjoiMjAyNC0wOC0yMlQwMzo1MTowNS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjUwNDkzNTYsInJnbiI6ImFwc2UyIn0.N4eRNlqjUPvY39J6bRbAG5x_omMPOB3AcmSpw3mpyys'  # Ensure your API key is correct
BOARD_ID = '1905613852'
MONDAY_API_URL = 'https://api.monday.com/v2'

headers = {
    'Authorization': MONDAY_API_KEY,
    'Content-Type': 'application/json'
}

required_columns = {
    "Work Order": "text",
    "Purchase Order": "numbers",
    "Customer": "text",
    "Location": "text",
    "Scheduled Date": "date",
    "Rate": "numbers",
    "SOW": "text",
    "Instructions": "text",
    "Vendor": "text",
    "Phone Number": "phone",
    "Shipping Terms": "text",
    "Payment Terms": "text",
    "Ordered By": "text",
    "Confirm By": "text",
    "Tax Code": "text",
    "FOB Location": "text",
    "Remarks": "text"
}

def extract_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    
    # Use regular expressions to extract all relevant data
    data = {
        'work_order': re.search(r'Work Order:\s*(\d+)', text),
        'purchase_order': re.search(r'P\.O\.\s*#:\s*(\d+)', text),
        'customer': re.search(r'Oneway Brunswick', text),
        'location': re.search(r'450 Warren Mason Blvd, Brunswick, GA 31520', text),
        'scheduled_date': re.search(r'\d{1,2}/\d{1,2}/\d{4}', text),
        'rate': re.search(r'\$\d+\.\d{2}', text),
        'sow': re.search(r'SOW\s*(.*?)\n', text, re.DOTALL),
        'instructions': re.search(r'Instructions:\s*(.*?)\n', text, re.DOTALL),
        'vendor': re.search(r'Vendor:\s*(.*?)\n', text, re.DOTALL),
        'phone_number': re.search(r'Phone(?: Number)?:\s*(\(\d{3}\)\s*\d{3}-\d{4})', text),
        'shipping_terms': re.search(r'Shipping Terms::\s*(.*?)\n', text),
        'payment_terms': re.search(r'Payment Terms:\s*(.*?)\n', text),
        'ordered_by': re.search(r'Ordered By:\s*(.*?)\n', text),
        'confirm_by': re.search(r'Confirm By:\s*(.*?)\n', text),
        'tax_code': re.search(r'Tax Code:\s*(.*?)\n', text),
        'fob_location': re.search(r'FOB Location:\s*(.*?)\n', text),
        'remarks': re.search(r'Remarks:\s*(.*?)\n', text),
    }

    # Extracted data needs to be cleaned up
    extracted_data = {}
    for key, match in data.items():
        if match:
            extracted_data[key] = match.group(1).strip() if match.lastindex else match.group().strip()
        else:
            extracted_data[key] = None
    
    # Additional cleanup for rate (remove $ sign)
    if extracted_data['rate']:
        extracted_data['rate'] = extracted_data['rate'].replace('$', '')
    
    # Fallback for SOW and instructions
    extracted_data['sow'] = extracted_data.get('sow', 'This is a test.')
    extracted_data['instructions'] = extracted_data.get('instructions', "Technician(s) must check in and out using the store's phone by calling 111-111-1111. Before/After photos required. Store Signature/Stamp required.")
    
    return extracted_data

def get_existing_columns():
    query = f'''
    {{
      boards(ids: {BOARD_ID}) {{
        columns {{
          id
          title
          type
        }}
      }}
    }}
    '''
    response = requests.post(MONDAY_API_URL, headers=headers, json={'query': query})
    if response.status_code == 200:
        columns = response.json()['data']['boards'][0]['columns']
        return {col['title']: col['id'] for col in columns}
    else:
        print("Failed to retrieve columns:", response.text)
        return {}

def create_monday_column(column_title, column_type):
    query = f'''
    mutation {{
      create_column (board_id: {BOARD_ID}, title: "{column_title}", column_type: {column_type}) {{
        id
        title
        type
      }}
    }}
    '''
    response = requests.post(MONDAY_API_URL, headers=headers, json={'query': query})
    if response.status_code == 200:
        print(f"Column '{column_title}' created successfully:", response.json())
    else:
        print(f"Failed to create column '{column_title}':", response.text)

def ensure_columns_exist():
    existing_columns = get_existing_columns()

    for title, col_type in required_columns.items():
        if title not in existing_columns:
            create_monday_column(column_title=title, column_type=col_type)
        else:
            print(f"Column '{title}' already exists.")

    return get_existing_columns()  # Retrieve updated column IDs

def create_monday_item(data, column_mapping):
    column_values = {
        column_mapping["Work Order"]: data['work_order'],
        column_mapping["Purchase Order"]: data['purchase_order'],
        column_mapping["Customer"]: data['customer'],
        column_mapping["Location"]: data.get('location', 'N/A'),
        column_mapping["Scheduled Date"]: data.get('scheduled_date', 'N/A'),
        column_mapping["Rate"]: data.get('rate', 'N/A'),
        column_mapping["SOW"]: data['sow'],
        column_mapping["Instructions"]: data['instructions'],
        column_mapping["Vendor"]: data.get('vendor', 'N/A'),
        column_mapping["Phone Number"]: data.get('phone_number', 'N/A'),
        column_mapping["Shipping Terms"]: data.get('shipping_terms', 'N/A'),
        column_mapping["Payment Terms"]: data.get('payment_terms', 'N/A'),
        column_mapping["Ordered By"]: data.get('ordered_by', 'N/A'),
        column_mapping["Confirm By"]: data.get('confirm_by', 'N/A'),
        column_mapping["Tax Code"]: data.get('tax_code', 'N/A'),
        column_mapping["FOB Location"]: data.get('fob_location', 'N/A'),
        column_mapping["Remarks"]: data.get('remarks', 'N/A'),
    }

    # Convert the dictionary to a JSON string
    column_values_json = json.dumps(column_values)

    query = f'''
    mutation {{
      create_item (board_id: {BOARD_ID}, item_name: "Work Order {data['work_order']} - {data['customer']}", column_values: "{column_values_json.replace('"', '\\"')}") {{
        id
      }}
    }}
    '''

    response = requests.post(MONDAY_API_URL, headers=headers, json={'query': query})
    if response.status_code == 200:
        print("Item created successfully:", response.json())
    else:
        print("Failed to create item:", response.text)

if __name__ == '__main__':
    # Step 1: Ensure columns exist
    column_mapping = ensure_columns_exist()

    # Step 2: Extract data from PDFs
    email_data = extract_data_from_pdf(r'Data/Test#2.pdf')
    work_order_data = extract_data_from_pdf(r'Data/Work Order.pdf')

    # Combine data from both sources
    combined_data = {**email_data, **work_order_data}

    # Step 3: Create item in Monday.com
    create_monday_item(combined_data, column_mapping)
