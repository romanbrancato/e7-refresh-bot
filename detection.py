import aircv as ac
import cv2
import easyocr


def locate_image(screenshot, reference):
    result = ac.find_template(screenshot, ac.imread(f"images/{reference}"), 0.90)
    return result['result'][:2] if result else None


def scan(ss):
    # Define the percentage of the ss height save
    crop_value = 8  # 8% of ss height
    height = int(ss.shape[0] * (crop_value / 100))

    # Crop the screenshot so only the top gold and ss symbol are visible
    cropped_ss = ss[:height, :]

    gold_img = ac.imread('images/gold.png')
    ss_img = ac.imread('images/ss.png')
    bag_img = ac.imread('images/bag.png')

    result_gold = ac.find_template(cropped_ss, gold_img)
    result_ss = ac.find_template(cropped_ss, ss_img)
    result_bag = ac.find_template(cropped_ss, bag_img)

    if result_gold is not None and result_ss is not None:
        # Get the rectangles from the results
        rect_gold = result_gold['rectangle']
        rect_ss = result_ss['rectangle']
        rect_bag = result_bag['rectangle']

        # Crop the image to isolate the region between the two symbols
        roi_gold = cropped_ss[:, rect_gold[0][0]:rect_ss[2][0]]
        roi_ss = cropped_ss[:, rect_ss[0][0]:rect_bag[2][0]]

        reader = easyocr.Reader(['en'])
        gold = reader.readtext(roi_gold)
        ss = reader.readtext(roi_ss)

        return gold[0][1].replace(",", ""), ss[0][1].replace(",", "")
