import glob
import os

import cv2
import numpy as np


def locate_image(screenshot, reference, threshold, edges=False, columns=None):
    # Only search between these x coordinates if given
    x_offset = 0
    if columns:
        x_offset = columns[0]
        screenshot = screenshot[:, columns[0]:columns[1]]

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
        center_x = max_loc[0] + w // 2 + x_offset
        center_y = max_loc[1] + h // 2

        result = {
            'result': (center_x, center_y),
            'rectangle': [
                (max_loc[0] + x_offset, max_loc[1]),
                (max_loc[0] + x_offset, max_loc[1] + h),
                (max_loc[0] + x_offset + w, max_loc[1] + h),
                (max_loc[0] + x_offset + w, max_loc[1])
            ],
            'confidence': max_val
        }

    return (result['result'] if result else None), max_val


def locate_all_images(screenshot, reference, threshold, columns=None, spacing=20):
    # Find every match above the threshold, returns the top-left corners sorted top to bottom
    x_offset = 0
    if columns:
        x_offset = columns[0]
        screenshot = screenshot[:, columns[0]:columns[1]]

    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    reference_gray = cv2.cvtColor(cv2.imread(f"images/{reference}"), cv2.COLOR_BGR2GRAY)
    result_match = cv2.matchTemplate(screenshot_gray, reference_gray, cv2.TM_CCOEFF_NORMED)

    matches = []
    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_match)
        if max_val < threshold:
            break
        matches.append((max_loc[0] + x_offset, max_loc[1]))
        # Blank out this match's rows so the next best is a different one
        result_match[max(0, max_loc[1] - spacing):max_loc[1] + spacing, :] = -1

    return sorted(matches, key=lambda match: match[1])


def text_hue(screenshot, x, y, w, h):
    # Median hue (0-180) of the colored text in a region, None if the text has no color
    region = cv2.cvtColor(screenshot[y:y + h, x:x + w], cv2.COLOR_RGB2HSV)
    colored = (region[:, :, 1] > 80) & (region[:, :, 2] > 100)
    if colored.sum() < 15:
        return None
    return int(np.median(region[:, :, 0][colored]))


def split_digits(region):
    # Cut a number into normalized grayscale images of each digit, left to right
    gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    if count < 2:
        return []

    # Commas and specks are much shorter than the digits
    tallest = stats[1:, cv2.CC_STAT_HEIGHT].max()
    boxes = sorted((s for s in stats[1:] if s[cv2.CC_STAT_HEIGHT] >= 0.6 * tallest), key=lambda s: s[0])

    digits = []
    for x, y, w, h, area in boxes:
        digit = gray[max(0, y - 1):y + h + 1, max(0, x - 1):x + w + 1].astype(np.float32)
        digit = (digit - digit.min()) / max(1, digit.max() - digit.min()) * 255
        # Scale to a fixed height keeping the shape, then center in a fixed width
        width = min(24, max(1, round(digit.shape[1] * 26 / digit.shape[0])))
        digit = cv2.resize(digit, (width, 26), interpolation=cv2.INTER_AREA)
        pad = 24 - width
        digits.append(cv2.copyMakeBorder(digit, 0, 0, pad // 2, pad - pad // 2, cv2.BORDER_CONSTANT, value=0))
    return digits


def read_number(region):
    # Read a whole number using the digit templates, None if any digit is uncertain
    templates = [(os.path.basename(path)[0], cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float32))
                 for path in glob.glob("images/digits/*.png")]
    text = ''
    for digit in split_digits(region):
        # Best score for each digit across all of its templates
        scores = {}
        for value, template in templates:
            score = cv2.matchTemplate(digit, template, cv2.TM_CCOEFF_NORMED)[0][0]
            scores[value] = max(score, scores.get(value, -1))
        ranked = sorted(scores, key=scores.get, reverse=True)

        # Refuse to guess if the match is weak or another digit is nearly as good
        if scores[ranked[0]] < 0.75 or scores[ranked[0]] - scores[ranked[1]] < 0.05:
            return None
        text += ranked[0]
    return int(text) if text else None


def has_speed(screenshot, es_label):
    # Whether the gear details popup has a speed substat
    # Only the substat rows directly above the "Equipment Score" row are searched,
    # leaving out the main stat above them and the set description below
    x, y = es_label
    region = cv2.cvtColor(screenshot[max(0, y - 100):y - 10, max(0, x - 70):x + 30], cv2.COLOR_RGB2GRAY)
    template = cv2.imread("images/speed.png", cv2.IMREAD_GRAYSCALE)
    return cv2.minMaxLoc(cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED))[1] >= 0.80


def is_boots(screenshot, es_label):
    # Whether the gear details popup's header says "Epic Boots"
    x, y = es_label
    region = cv2.cvtColor(screenshot[max(0, y - 330):max(1, y - 150), max(0, x - 60):x + 200], cv2.COLOR_RGB2GRAY)
    template = cv2.imread("images/epic_boots.png", cv2.IMREAD_GRAYSCALE)
    return cv2.minMaxLoc(cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED))[1] >= 0.75
