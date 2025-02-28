from flask import Flask, request, jsonify, render_template
import re
from urllib.parse import urlparse
import json

app = Flask(__name__)

# Define URL patterns for different categories
edu_patterns = [
    r'\.edu$',
    r'\.edu\.[a-z]{2}$',  # For international edu domains like .edu.au
    r'\.ac\.[a-z]{2}$',   # For academic domains like .ac.uk
    r'\.(edu|ac)\.',      # For variations of educational domains
]

gov_patterns = [
    r'\.gov$',
    r'\.gov\.[a-z]{2}$',  # For international gov domains
    r'\.mil$',           # For military domains
    r'\.(gov|mil)\.',    # For variations of government domains
]

org_patterns = [
    r'\.org$',
    r'\.org\.[a-z]{2}$',  # For international org domains
    r'\.(int|museum)$',  # For international organization domains
    r'\.(org|int)\.',    # For variations of organization domains
]

def extract_links(text):
    """Extract complete and accurate URLs from text with high precision."""
    try:
        # Use a precise approach that prioritizes complete URLs
        extracted_urls = []
        
        # First, extract fully qualified URLs with protocol (most reliable)
        protocol_pattern = r'https?://[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        protocol_urls = re.findall(protocol_pattern, text)
        
        # Process each URL to ensure it's valid and normalized
        for url in protocol_urls:
            try:
                # Basic validation - must have proper domain structure
                parsed = urlparse(url)
                if parsed.netloc and '.' in parsed.netloc:
                    # Keep the URL in its original form to avoid formatting issues
                    if url not in extracted_urls:
                        extracted_urls.append(url)
            except Exception as e:
                print(f"Error validating URL {url}: {str(e)}")
        
        # Only if we have a very small number of URLs, try to extract URLs without protocol
        # as a fallback, but with very strict validation
        if len(extracted_urls) < 2:
            # Look for www. prefixed URLs with strict boundaries to avoid partial matches
            www_pattern = r'(?<![:/\w])www\.[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[-a-zA-Z0-9()@:%_\+.~#?&//=]*)?'
            www_urls = re.findall(www_pattern, text)
            
            for url in www_urls:
                full_url = 'https://' + url
                if not any(url in existing for existing in extracted_urls) and full_url not in extracted_urls:
                    extracted_urls.append(full_url)
                    
            # Only as a last resort, look for domains without www but with common TLDs
            if len(extracted_urls) < 2:
                domain_pattern = r'(?<![:/\.\w])[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.(com|org|edu|gov|net)(?:\.[a-zA-Z]{2,})?(?:/[-a-zA-Z0-9()@:%_\+.~#?&//=]*)?'
                domain_urls = re.findall(domain_pattern, text)
                
                for url_tuple in domain_urls:
                    url = url_tuple[0] if isinstance(url_tuple, tuple) else url_tuple
                    full_url = 'https://www.' + url
                    if not any(url in existing for existing in extracted_urls) and full_url not in extracted_urls:
                        extracted_urls.append(full_url)
        
        print(f"Extracted {len(extracted_urls)} unique URLs")
        return extracted_urls
    except Exception as e:
        print(f'Error in extract_links: {str(e)}')
        return []

def categorize_links(urls):
    """Categorize links by domain type."""
    try:
        categorized = {
            "edu": [],
            "gov": [],
            "org": [],
            "com": [],
            "net": [],
            "other": [],
            "duplicate_summary": {
                "total_duplicates": 0,
                "duplicate_urls": {}
            }
        }
        
        for url in urls:
            try:
                # Parse the URL to get the domain
                parsed_url = urlparse(url)
                if not parsed_url.netloc:
                    print(f'Invalid URL format: {url}')
                    continue
                    
                domain = parsed_url.netloc.lower()
                
                # Categorize the URL
                if any(re.search(pattern, domain) for pattern in edu_patterns):
                    categorized["edu"].append(url)
                elif any(re.search(pattern, domain) for pattern in gov_patterns):
                    categorized["gov"].append(url)
                elif any(re.search(pattern, domain) for pattern in org_patterns):
                    categorized["org"].append(url)
                elif '.com' in domain:
                    categorized["com"].append(url)
                elif '.net' in domain:
                    categorized["net"].append(url)
                else:
                    categorized["other"].append(url)
                    
            except Exception as e:
                print(f'Error processing URL {url}: {str(e)}')
                categorized["other"].append(url)
        
        return categorized
    except Exception as e:
        print(f'Error in categorize_links: {str(e)}')
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Invalid request format. Please provide text data.'}), 400
            
        text = data.get('text', '')
        if not text.strip():
            return jsonify({'error': 'Empty text provided. Please provide some text with links.'}), 400
        
        # Extract links from the text
        urls = extract_links(text)
        if not urls:
            return jsonify({'error': 'No valid URLs found in the provided text.'}), 400
        
        # Categorize links
        categorized = categorize_links(urls)
        
        # Log count of links for debugging
        total_links = sum(len(categorized[cat]) for cat in categorized if cat != "duplicate_summary")
        print(f"Total unique links processed: {total_links}")
        
        return jsonify(categorized)
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format in request.'}), 400
    except Exception as e:
        print(f'Error processing links: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred while processing the links.'}), 500

if __name__ == '__main__':
    app.run(debug=True)