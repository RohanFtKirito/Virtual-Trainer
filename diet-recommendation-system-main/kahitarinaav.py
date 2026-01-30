import pickle
import json

# Load the pickled file
with open('C:/Users/Pratham/Downloads/zacson-master (1)/zacson-master/diet-recommendation-system-main/food_model.pickle', 'rb') as f:

    data = pickle.load(f)

coefficients = data['model'].coef_.tolist()[0]  # Convert coefficients to a list
intercept = data['model'].intercept_.tolist()[0]  # Convert intercept to a list

# Create a dictionary to store the serialized model
serialized_model = {
    'coefficients': coefficients,
    'intercept': intercept,
    # Add other necessary information about the model
}

# Convert the serialized model data to JSON
json_model = json.dumps(serialized_model, indent=4)

# Save the JSON data to a file
with open("food_model.json", "w") as f:
    f.write(json_model)