# -*- coding: utf-8 -*-
"""
Simple web interface for WikiTranslateAI demo
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Flask not installed. Run: pip install flask")
    sys.exit(1)

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "wikitranslate-demo"

SUPPORTED_LANGUAGES = {
    'yor': 'Yoruba',
    'fon': 'Fon', 
    'ewe': 'Ewe',
    'dindi': 'Dindi'
}

@app.route('/')
def home():
    """Home page with simple HTML"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WikiTranslateAI Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
            h1 { color: #007cba; text-align: center; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"] { width: 100%%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .languages { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0; }
            .lang-option label { font-weight: normal; }
            button { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
            .info { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>WikiTranslateAI Demo</h1>
            <p>Translate Wikipedia articles to African languages</p>
            
            <form action="/translate" method="post">
                <div class="form-group">
                    <label for="title">Wikipedia Article Title (French):</label>
                    <input type="text" id="title" name="title" placeholder="e.g., Ordinateur, France..." required>
                </div>
                
                <div class="form-group">
                    <label>Target Language:</label>
                    <div class="languages">
                        <div class="lang-option">
                            <input type="radio" id="yor" name="language" value="yor" required>
                            <label for="yor">Yoruba</label>
                        </div>
                        <div class="lang-option">
                            <input type="radio" id="fon" name="language" value="fon" required>
                            <label for="fon">Fon</label>
                        </div>
                        <div class="lang-option">
                            <input type="radio" id="ewe" name="language" value="ewe" required>
                            <label for="ewe">Ewe</label>
                        </div>
                        <div class="lang-option">
                            <input type="radio" id="dindi" name="language" value="dindi" required>
                            <label for="dindi">Dindi</label>
                        </div>
                    </div>
                </div>
                
                <button type="submit">Start Translation</button>
            </form>
            
            <div class="info">
                <strong>Demo Info:</strong> This is a demonstration interface for WikiTranslateAI. 
                The system specializes in translating Wikipedia articles to underrepresented African languages 
                with cultural preservation and tonal accuracy.
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/translate', methods=['POST'])
def translate():
    """Translation page"""
    title = request.form.get('title', '').strip()
    language = request.form.get('language', '')
    
    if not title or not language:
        return "Error: Please provide both title and language"
    
    # Simple demo response
    translations = {
        'yor': {'Ordinateur': 'Kọmputa', 'France': 'Fransi'},
        'fon': {'Ordinateur': 'Kɔmputà', 'France': 'Fɛnsi'},
        'ewe': {'Ordinateur': 'Kɔmputa', 'France': 'Frans'},
        'dindi': {'Ordinateur': 'Kwamfuta', 'France': 'Faransa'}
    }
    
    translated_title = translations.get(language, {}).get(title, title)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Translation Result - WikiTranslateAI</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
            h1 {{ color: #007cba; }}
            .result {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .back {{ margin: 20px 0; }}
            a {{ color: #007cba; text-decoration: none; }}
            .demo-note {{ background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="back"><a href="/">&larr; Back to Home</a></div>
            
            <h1>Translation Preview</h1>
            
            <div class="result">
                <h3>Original: {title}</h3>
                <h3>Translated: {translated_title}</h3>
                <p><strong>Target Language:</strong> {SUPPORTED_LANGUAGES.get(language, language)}</p>
                <p><strong>Status:</strong> Demo simulation</p>
            </div>
            
            <div class="demo-note">
                <strong>Demo Note:</strong> This is a simplified demonstration. 
                The full system would perform:
                <ul>
                    <li>Wikipedia article extraction</li>
                    <li>Intelligent text segmentation</li>
                    <li>AI-powered translation with cultural awareness</li>
                    <li>Tonal accuracy optimization</li>
                    <li>Article reconstruction</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'supported_languages': list(SUPPORTED_LANGUAGES.keys())
    })

if __name__ == '__main__':
    print("Starting WikiTranslateAI demo server...")
    app.run(host='127.0.0.1', port=5000, debug=True)