import requests
import json
from config import get_api_key

def fetch_medication_info(medication_name):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {get_api_key()}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'user', 'content': f'Provide information about the medication: {medication_name}'}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f'Error fetching data: {response.status_code}, {response.text}')

def fetch_contraindications(medications):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {get_api_key()}',
        'Content-Type': 'application/json'
    }
    query = f'Are there any contraindications for this combination of medicines ({', '.join(medications)})? If so, list them in a table format from most serious to least serious. Each row should have two columns: Seriousness and Description. Use the following seriousness levels: Very Serious, Serious, Moderate, Minor.'
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'user', 'content': query}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        return parse_contraindications(content)
    except requests.exceptions.RequestException as e:
        raise Exception(f'Error fetching data: {str(e)}')
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise Exception(f'Error parsing API response: {str(e)}')

def parse_contraindications(content):
    lines = content.split('\n')
    contraindications = []
    
    start_index = next((i for i, line in enumerate(lines) if '|' in line), 0) + 1
    
    for line in lines[start_index:]:
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                seriousness = parts[1].strip()
                description = parts[2].strip()
                contraindications.append({
                    'seriousness': seriousness,
                    'description': description
                })
    
    return contraindications if contraindications else [{'seriousness': 'N/A', 'description': 'No contraindications found.'}]

def fetch_medication_description(medication_name):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {get_api_key()}',
        'Content-Type': 'application/json'
    }
    query = f"Just list from most often used to treat to least often used to treat, nothing else, the disorders that {medication_name} is used to treat."
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'user', 'content': query}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        return content.strip()
    except requests.exceptions.RequestException as e:
        raise Exception(f'Error fetching data: {str(e)}')
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise Exception(f'Error parsing API response: {str(e)}')

def chat_with_gpt(medications, user_input):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {get_api_key()}',
        'Content-Type': 'application/json'
    }
    
    system_prompt = f"I am taking the following medications: {medications}. I have some questions about the medication."
    
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_input}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        return content.strip()
    except requests.exceptions.RequestException as e:
        raise Exception(f'Error fetching data: {str(e)}')
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise Exception(f'Error parsing API response: {str(e)}')

def get_greeting(medications):
    medication_names = [med.split(' (')[0] for med in medications.split(', ')]
    return f"Hello, I'm here to assist you. I understand that you're taking {', '.join(medication_names)}. How can I help you?"
