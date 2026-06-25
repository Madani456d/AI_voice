import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

# 1. Correctly load your specific environment file
load_dotenv(dotenv_path='key.env')

MURF_API_KEY = os.getenv("MURF_API_KEY")

app = Flask(__name__)

API_MODEL = 'falcon-2'
HEADERS = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}

# Robust voice parsing that handles lists or dictionaries
def parse_voices(response):
    if response.status_code == 200:
        data = response.json()
        return data if isinstance(data, list) else data.get('data', [])
    print(f"DEBUG: API failed ({response.status_code}): {response.text}")
    return []

@app.route('/', methods=['GET'])
def index():
    # 2. Explicitly include model=falcon-2
    url = f"https://api.murf.ai/v1/speech/voices?model={API_MODEL}"
    response = requests.get(url, headers={"api-key": MURF_API_KEY})
    voices = parse_voices(response)
    return render_template('index.html', voices=voices)

@app.route('/generate', methods=['POST'])
def generate():
    script_text = request.form.get('text', '')
    selected_voice = request.form.get('voiceId')
    rate = int(request.form.get('rate', 0))
    pitch = int(request.form.get('pitch', 0))

    payload = {
        "text": script_text,
        "voiceId": selected_voice,
        "model": API_MODEL, 
        "rate": rate,
        "pitch": pitch,
        "locale": "en-US",
        "format": "WAV"
    }

    response = requests.post(
        "https://api.murf.ai/v1/speech/stream", 
        json=payload, 
        headers=HEADERS, 
        stream=True
    )

    if response.status_code == 200:
        output_path = os.path.join('static', 'output.wav')
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Re-fetch voices to keep dropdown populated
        url = f"https://api.murf.ai/v1/speech/voices?model={API_MODEL}"
        voices_resp = requests.get(url, headers={"api-key": MURF_API_KEY})
        voices = parse_voices(voices_resp)
        
        return render_template('index.html', audio_file='output.wav', voices=voices)
    else:
        return f"Error: {response.text}", response.status_code

if __name__ == '__main__':
    app.run(debug=True, port=5000)