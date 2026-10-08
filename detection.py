import cv2


def locate_image(screenshot, reference, threshold, edges=False):
    # Load the reference image
    reference_img = cv2.imread(f"images/{reference}")

    if edges:
        # Convert to grayscale and apply edge detection
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        reference_gray = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
        screenshot_processed = cv2.Canny(screenshot_gray, 50, 150)
        reference_processed = cv2.Canny(reference_gray, 50, 150)
    else:
        # Convert to grayscale for template matching
        screenshot_processed = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        reference_processed = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)

    # Template matching
    result_match = cv2.matchTemplate(screenshot_processed, reference_processed, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_match)

    # Check if match is above threshold
    result = None
    if max_val >= threshold:
        h, w = reference_processed.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        result = {
            'result': (center_x, center_y),
            'rectangle': [
                (max_loc[0], max_loc[1]),
                (max_loc[0], max_loc[1] + h),
                (max_loc[0] + w, max_loc[1] + h),
                (max_loc[0] + w, max_loc[1])
            ],
            'confidence': max_val
        }

    return (result['result'] if result else None), max_val

