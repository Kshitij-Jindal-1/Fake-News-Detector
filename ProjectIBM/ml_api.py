from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import joblib

# Load model and tokenizer
model = load_model("cnn_model.h5")
tokenizer = joblib.load("tokenizer.pkl")
max_len = 300

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# ✅ Basic health check route
@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Fake News Detection API is running 🚀'}), 200

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    # Accept both 'text' and 'url'
    text = data.get('text') or data.get('url') or ''
    if not text.strip():
        return jsonify({'error': 'No text or URL provided', 'received': data}), 400

    try:
        # Preprocess
        seq = tokenizer.texts_to_sequences([text])
        padded = pad_sequences(seq, maxlen=max_len, padding='post')

        # Predict
        prob = float(model.predict(padded).squeeze())
        prediction = "True" if prob > 0.5 else "Fake"

        return jsonify({'prediction': prediction, 'probability': prob})
    except Exception as e:
        print("❌ Prediction error:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
