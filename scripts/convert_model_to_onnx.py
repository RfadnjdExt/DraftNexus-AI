import joblib
import numpy as np
import os
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
MODEL_PATH = os.path.join(DATA_DIR, 'draft_model_rf.pkl')
ONNX_PATH = os.path.join(DATA_DIR, 'draft_model.onnx')

def convert_model():
    if not os.path.exists(MODEL_PATH):
        print("Model file not found!")
        return

    print("Loading Scikit-Learn Model...")
    clf = joblib.load(MODEL_PATH)
    
    # Define Input Type
    # Our feature vector size depends on training.
    # We need to check n_features_in_
    n_features = clf.n_features_in_
    print(f"Model expects {n_features} input features.")
    
    # 'float_input' matches the name expected by the initial types
    # Size: [None, n_features] where None means batch size is variable
    initial_type = [('float_input', FloatTensorType([None, n_features]))]

    print("Converting to ONNX (Opset 15, ZipMap=False)...")
    # Target Opset 15 is safe for onnxruntime-android 1.16.0
    # zipmap=False ensures probabilities are returned as a raw Float Tensor, not a ZipMap
    bg_node = convert_sklearn(clf, initial_types=initial_type, target_opset=15, options={'zipmap': False})
    
    # Force IR Version 9 (Max supported by Android ORT 1.16 in some cases)
    bg_node.ir_version = 9

    with open(ONNX_PATH, "wb") as f:
        f.write(bg_node.SerializeToString())
        
    print(f"Success! Model saved to {ONNX_PATH}")

def verify_onnx():
    print("Verifying ONNX Model...")
    sess = rt.InferenceSession(ONNX_PATH)
    
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    
    # Create dummy input with correct shape
    # We need to know the shape (read from model or assume from above)
    # Let's just reload the pickle to be lazy about shape, or assume 272 (131+131+5+10 etc)
    clf = joblib.load(MODEL_PATH)
    n_features = clf.n_features_in_
    
    dummy_input = np.random.rand(1, n_features).astype(np.float32)
    
    # Run Inference
    pred_onx = sess.run([label_name], {input_name: dummy_input})[0]
    
    # Run Sklearn Inference
    pred_skl = clf.predict(dummy_input)
    
    print(f"Sklearn Prediction: {pred_skl[0]}")
    print(f"ONNX Prediction: {pred_onx[0]}")
    
    if pred_skl[0] == pred_onx[0]:
        print("✅ Conversion Verified: Output Matches")
    else:
        print("❌ Mismatch!")

if __name__ == "__main__":
    convert_model()
    verify_onnx()
