import os
import cv2


def locate_image(reference, client_index):
    #  Load screenshot
    screenshot_path = os.path.expandvars(
        os.path.join(os.path.expanduser('~'), 'Documents', 'XuanZhi9', 'Pictures', f'ss{client_index}.png'))
    screen = cv2.imread(screenshot_path)

    # Load reference image
    reference_path = "detection\\images\\" + reference
    image = cv2.imread(reference_path)

    # Get dimensions of reference image
    try:
        h, w = image.shape[0], image.shape[1]
    except:
        raise Exception("Image not found in given path.")

    # Matches the reference image to the screenshot
    result = cv2.matchTemplate(screen, image, cv2.TM_CCOEFF_NORMED)

    # '''Shows area its located'''''
    # threshold = 0.8
    # loc = np.where(result >= threshold)
    # for pt in zip(*loc[::-1]):
    #     cv2.rectangle(screen, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
    #
    # cv2.imshow("Detection Result", screen)
    # cv2.waitKey(3000)
    # ''''''''''''''''''''''''''''''

    # Find the position of the best match
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Calculate the center point of the matched rectangle
    if max_val > 0.90:
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        center = ((top_left[0] + bottom_right[0]) // 2, (top_left[1] + bottom_right[1]) // 2)
        print(f'{os.path.basename(reference)} found')
        return center

    else:
        print(f'{os.path.basename(reference)} not found')
        return None
