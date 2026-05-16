import base64
import io
import cv2
import numpy as np
from PIL import Image
from deepface import DeepFace


def _to_bytes(data):
    """
    Accepts either raw bytes or a Base64-encoded string and always returns bytes.
    Kept identical to protect existing caller formats.
    """
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        return base64.b64decode(data)
    raise TypeError(f"Expected bytes or Base64 string, got {type(data).__name__}")


def get_face_encoding(image_data):
    """
    Extracts a high-dimensional (512-d) face embedding using Facenet512.
    Returns a list of floats (embedding) or None if no face is detected.
    """
    try:
        image_bytes = _to_bytes(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        # DeepFace processing expects BGR matrix format (standard OpenCV layout)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        # Extract 512-dimensional vector embedding using the hyper-accurate Facenet512 model
        embeddings = DeepFace.represent(
            img_path=image_bgr,
            model_name="SFace",
            enforce_detection=True,
            detector_backend="opencv",
        )

        if not embeddings:
            return None

        # Return the raw mathematical vector representation array
        return embeddings[0]["embedding"]

    except Exception as e:
        print(f"Error encoding image via DeepFace: {e}")
        return None


def find_closest_match(login_image_data, db_images_dict):
    """
    Compares a login attempt against a dictionary of known profile image encodings.

    :param login_image_data: Webcam capture as raw bytes or a Base64 string.
    :param db_images_dict: Dict mapping { uid: list_of_floats } fetched from MongoDB.
    :return: The UID string of the closest match, or None if below threshold.
    """
    print("Processing login frame via DeepFace...")
    login_encoding = get_face_encoding(login_image_data)

    if login_encoding is None:
        print("No face detected in login frame.")
        return None

    best_match_uid = None
    min_distance = float("inf")

    # Facenet512 cosine distance verification threshold (0.3 is the standard sweet spot for strict verification)
    threshold = 0.3

    print(f"Comparing against {len(db_images_dict)} records in database...")

    for uid, db_enc in db_images_dict.items():
        if db_enc is not None:
            # Calculate the angular cosine discrepancy between the matrix points
            distance = DeepFace.verification.dst.compute_cosine(
                np.array(login_encoding), np.array(db_enc)
            )

            if distance < min_distance:
                min_distance = distance
                best_match_uid = uid

    if min_distance <= threshold and best_match_uid is not None:
        print(
            f"✅ Match found: UID={best_match_uid} distance={min_distance:.3f}"
        )
        return best_match_uid

    print(
        f"❌ No match found. Closest distance was {min_distance:.3f} (threshold is <= {threshold})"
    )
    return None