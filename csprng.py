import cv2
import hashlib
import numpy as np

def generate_key_from_frame(frame, roi_coords, block_size=256):
    """
    Generates a 256-bit secure key from a single video frame.
    
    Args:
        frame (np.ndarray): The input video frame.
        roi_coords (tuple): (x, y, w, h) for the region of interest.
        block_size (int): The number of raw bits to use for hashing.
        
    Returns:
        str: A 64-character hexadecimal string representing the 256-bit key.
             Returns None if the frame is invalid.
    """
    x, y, w, h = roi_coords
    
    # 1. Pre-processing: Extract ROI and convert to grayscale
    if frame is None or frame.size == 0:
        return None
    roi = frame[y:y+h, x:x+w]
    if roi.size == 0:
        return None
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 2. Entropy Extraction: Get LSBs
    # The bitwise AND with 1 isolates the least significant bit
    lsb_plane = gray_roi & 1
    
    # 3. Flatten the LSB plane to a 1D array of bits
    raw_bits = lsb_plane.flatten()
    
    # 4. Whitening: Hash the first `block_size` bits
    if len(raw_bits) < block_size:
        return None # Not enough entropy in this frame
        
    # Convert the first N bits to a string of '0's and '1's
    bit_string = "".join(map(str, raw_bits[:block_size]))
    
    # Hash the bit string using SHA-256
    hasher = hashlib.sha256()
    hasher.update(bit_string.encode('utf-8'))
    
    # Return the hexadecimal digest
    return hasher.hexdigest()

# --- Example Usage ---
if __name__ == '__main__':
    # Initialize the default camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Cannot open camera.")
        exit()
        
    # Define a Region of Interest (e.g., 320x240 pixels from the top-left)
    ROI = (0, 0, 320, 240)
    
    print("Generating keys... Press Ctrl+C to stop.")
    try:
        while True:
            ret, frame = cap.read()
            if ret:
                key = generate_key_from_frame(frame, ROI)
                if key:
                    print(f"Generated Secure Key: {key}")
            else:
                print("Failed to grab frame.")
                break
    except KeyboardInterrupt:
        print("\nStopping key generation.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
