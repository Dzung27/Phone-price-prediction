from flask import Flask, request, render_template, jsonify
import joblib
import numpy as np
import os

app = Flask(__name__)

model_directory = {
    'Stacking Regressor with KNN': 'models/stacking_regressor_with_knn',
    'Random Forest': 'models/random_forest',
    'Gradient Boost': 'models/gradient_boost',
    'XG Boost': 'models/xg_boost',
}

@app.route('/', methods=['GET'])
def home():
    # We dynamically generate model options and brands based on directory structure
    model_options = list(model_directory.keys())
    brands = set()
    for dir in model_directory.values():
        brands.update([file.split('_')[0] for file in os.listdir(dir) if 'stacking_model' in file])
    brands = list(brands)
    print("Model Options:", model_options)  # Debug output
    print("Brands:", brands)  # Debug output

    metrics = ['mm', 'mm', 'mm', 'g', 'Type', 'mAh', 'inches', 'px', 'px', 'cores', 'GB', 'GB', 'Yes(1)/No(0)']
    names = ['length', 'width', 'thickness', 'weight', 'battery_type', 'battery_capacity', 'screen_size',
             'resolution_height', 'resolution_width', 'cpu_cores', 'internal_storage', 'ram', 'nfc_support']
    name_metric_pairs = list(zip(names, metrics))

    # Added name_metric_pairs to the rendering context
    return render_template('home.html', model_options=model_options, brands=brands, name_metric_pairs=name_metric_pairs)

@app.route('/predict', methods=['POST'])
def predict():

    data = request.form
    required_fields = ['length', 'width', 'thickness', 'weight', 'battery_type',
                       'battery_capacity', 'screen_size', 'resolution_height',
                       'resolution_width', 'cpu_cores', 'internal_storage', 'ram', 'nfc_support']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'Missing or empty field: {field}'}), 400

    selected_model = data['model_option']
    brand = data['brand']

    # Build paths to the model and scaler files
    model_path = os.path.join(model_directory[selected_model], f"{brand}_stacking_model.pkl")
    scaler_path = os.path.join(model_directory[selected_model], f"{brand}_scaler.pkl")

    # Load the selected model and scaler
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        # Collect features from the form
        features = np.array([[
            data['length'], data['width'], data['thickness'], data['weight'],
            data['battery_type'], data['battery_capacity'], data['screen_size'],
            data['resolution_height'], data['resolution_width'], data['cpu_cores'],
            data['internal_storage'], data['ram'], data['nfc_support']
        ]], dtype=float)

        # Scale the features and predict
        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)
        return jsonify({'prediction': f'${prediction[0]:.2f}'})
    else:
        return jsonify({'error': 'Model or scaler not found for the selected brand and model.'})

if __name__ == '__main__':
    app.run(debug=True)
