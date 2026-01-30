import numpy as np
import onnxruntime as ort
import joblib
import os
import sys

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '../data')
PKL_PATH = os.path.join(DATA_DIR, 'draft_model_rf.pkl')
ONNX_PATH = os.path.join(DATA_DIR, 'draft_model.onnx')

def compare_models():
    print(f"Loading PKL from: {PKL_PATH}")
    try:
        clf_pkl = joblib.load(PKL_PATH)
    except Exception as e:
        print(f"Error loading PKL: {e}")
        return

    print(f"Loading ONNX from: {ONNX_PATH}")
    try:
        ort_session = ort.InferenceSession(ONNX_PATH)
    except Exception as e:
        print(f"Error loading ONNX: {e}")
        return

    # Generate Random Input
    # Feature size is 277 (based on Android code and previous knowledge)
    input_size = 277 
    # Create N random inputs
    N = 5
    dummy_input = np.random.rand(N, input_size).astype(np.float32)
    
    # 1. Prediction via PKL (Sklearn)
    print("\nRunning PKL Inference...")
    # predict_proba returns [N, 2] usually (for binary)
    pkl_probs = clf_pkl.predict_proba(dummy_input).astype(np.float32)
    
    # 2. Prediction via ONNX
    print("Running ONNX Inference...")
    input_name = ort_session.get_inputs()[0].name
    # Output 1 is usually probabilities in sklearn-onnx conversion
    # Result is a list, usually [label_tensor, probability_tensor]
    # For ZipMap=False output is usually a tensor.
    # Let's inspect outputs.
    # If produced by sklearn-onnx, output[1] is typically 'output_probability' (sequence of maps OR tensor if zipmap=False)
    
    onnx_results = ort_session.run(None, {input_name: dummy_input})
    
    # We expect the second output to be probabilities
    # But it depends on how it was exported.
    # Let's assume standard sklearn-onnx conversion with final_types
    # If zipmap=True (default), it's a list of dicts. If False, it's a tensor.
    
    onnx_probs = None
    
    # Check type of second output
    raw_out = onnx_results[1]
    
    if isinstance(raw_out, list) and isinstance(raw_out[0], dict):
        print("ONNX Output is ZipMap (List of Dicts). Converting to Tensor...")
        # Convert list of dicts to tensor [N, 2]
        # Dict be like {0: prob_0, 1: prob_1}
        # Assuming binary classification classes are 0 and 1
        probs_list = []
        for d in raw_out:
            p0 = d.get(0, 0.0)
            p1 = d.get(1, 0.0)
            probs_list.append([p0, p1])
        onnx_probs = np.array(probs_list, dtype=np.float32)
        
    elif isinstance(raw_out, np.ndarray):
        print("ONNX Output is Tensor.")
        onnx_probs = raw_out.astype(np.float32)
        
    else:
        print(f"Unknown ONNX output format: {type(raw_out)}")
        print(raw_out)
        return

    print(f"\nComparing {N} samples...")
    print(f"{'Sample':<6} | {'PKL Probs':<20} | {'ONNX Probs':<20} | {'Diff':<10}")
    print("-" * 65)

    max_diff = 0.0
    for i in range(N):
        p_pkl = pkl_probs[i]
        p_onnx = onnx_probs[i]
        
        # Compare prediction for class 1 (usually what acts as score)
        diff = np.abs(p_pkl - p_onnx).max()
        max_diff = max(max_diff, diff)
        
        # Fmt
        s_pkl = f"[{p_pkl[0]:.4f}, {p_pkl[1]:.4f}]"
        s_onnx = f"[{p_onnx[0]:.4f}, {p_onnx[1]:.4f}]"
        
        print(f"{i:<6} | {s_pkl:<20} | {s_onnx:<20} | {diff:.6f}")

    print("-" * 65)
    print(f"Max Absolute Difference: {max_diff:.8f}")
    
    if max_diff < 1e-5:
        print("\n✅ MATCH: Models are effectively identical.")
    else:
        print("\n⚠️ MISMATCH: Significant difference found.")

if __name__ == "__main__":
    compare_models()
