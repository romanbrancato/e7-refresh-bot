from threading import Event
from time import sleep, time

from detection import *


class Bot:
    REFRESH_BUTTON_COORD = (150, 495)
    BUY_BUTTON_COORD = (415, 20)  # Values added to x and y of currency image location
    CURRENCY_COLUMN = (412, 492)  # x range of the shop's item icons, excludes popups in the middle
    RETRY_TIMEOUT = 1.5  # Seconds to wait for a click to take effect before clicking again
    GEAR_LABEL_COLUMN = (505, 610)  # x range of the "Equipment" labels in the shop
    GEAR_BUY_BUTTON_X = 866
    GEAR_BUY_BUTTON_OFFSET = 49  # y distance from the "Equipment" label to its row's buy button
    DIALOG_COLUMN = (440, 700)  # x range of the buy dialog's confirm button, excludes the shop's buttons
    GEAR_ICON_X = 451
    GEAR_ICON_OFFSET = 41  # y distance from the "Equipment" label to the center of its row's icon
    CLOSE_MENU_COORD = (150, 150)  # Empty spot outside the acquired menu, tapping it closes the menu
    # Before scrolling only the top two rows are bought, any lower and their greyed out buy buttons
    # would still be on screen after scrolling and stop scroll_success from matching
    TOP_ROWS_MAX_Y = 250
    BANNER_TIME = 2.5  # Seconds the banner shown after a purchase covers the top row

    def __init__(self, client, config):
        self.client = client
        # Only tracked when stopping on a skystone/gold limit
        self.ss = config["ss"]
        self.gold = config["gold"]
        self.stop_condition = config["stop_condition"]

        self.currencies = {"bm": {"quantity": 5, "cost": 184000, "count": 0, "bought": False},
                           "mm": {"quantity": 50, "cost": 280000, "count": 0, "bought": False}}
        if config["fs"]:
            self.currencies["fs"] = {"quantity": 50, "cost": 18000, "count": 0, "bought": False}
        self.gear = config["gear"]
        self.gear_sold = 0
        self.epic_mode = config["epic"]["mode"]  # "ignore", "pause" or "buy"
        self.min_es = config["epic"]["min_es"]  # None buys every epic
        self.speed = config["epic"]["speed"]  # Always buy epics with speed, whatever their ES
        self.epic_bought = 0
        self.handled_epics = []  # Rows already paused on or skipped this refresh

        # Set by the GUI's resume button while paused
        self.paused = False
        self.resume_event = Event()
        self.refreshes = 0
        self.last_purchase = 0  # When the last purchase finished, its banner covers the top row for a while
        self.status = "Starting"  # Current action, shown in the GUI

    def locate(self, screenshot, reference, threshold, edges=False, columns=None):
        name = reference.removesuffix('.png')
        self.status = f"Locating: {name}"
        location, confidence = locate_image(screenshot, reference, threshold, edges, columns)
        self.status = f"Locating: {name} ({confidence:.3f})"
        return location

    def click(self, point, name):
        self.status = f"Clicking: {name}"
        self.client.click(point)

    def wait_for(self, reference, threshold, timeout=None, edges=False, columns=None, settled=False):
        # Take screenshots until the image appears or the timeout passes
        # If settled, the image must also be in the same spot twice in a row, for menus that ignore taps while moving
        start = time()
        previous = None
        while True:
            screenshot = self.client.capture_screen()
            location = self.locate(screenshot, reference, threshold, edges, columns)
            if location and (not settled or location == previous):
                return location, screenshot
            if timeout is not None and time() - start >= timeout:
                return None, screenshot
            previous = location

    def handle_refresh(self):
        scrolled = False
        screenshot = self.client.capture_screen()
        while self.continue_refreshing():
            # Purchases made after the last scroll leave a banner over the top row of the refreshed shop
            if not scrolled and self.wait_for_banner():
                screenshot = self.client.capture_screen()
            self.locate_and_buy(screenshot, None if scrolled else self.TOP_ROWS_MAX_Y)
            if not scrolled:
                screenshot = self.perform_scroll()
            else:
                screenshot = self.perform_refresh()
            scrolled = not scrolled

    def wait_for_banner(self):
        # Wait out the rest of the last purchase's banner, returns whether it waited
        remaining = self.BANNER_TIME - (time() - self.last_purchase)
        if remaining <= 0:
            return False
        self.status = f"Waiting: purchase banner ({remaining:.1f}s)"
        sleep(remaining)
        return True

    def continue_refreshing(self):
        currency = self.stop_condition["currency"]
        amount = self.stop_condition["amount"]

        if currency == "ss":
            # Only refresh if it won't drop skystones below the limit
            return self.ss - 3 >= amount

        if currency == "gold":
            # Only refresh if there's enough gold above the limit to buy a bookmark or mystic medal
            return self.gold - min(self.currencies[c]["cost"] for c in ("bm", "mm")) >= amount

        return amount == 0 or self.currencies[currency]["count"] < amount

    def can_afford(self, currency):
        # Skip purchases that would drop gold below the limit
        if self.gold is None:
            return True
        return self.gold - self.currencies[currency]["cost"] >= self.stop_condition["amount"]

    def locate_and_buy(self, screenshot, max_y=None):
        # Locate all available currencies, only above max_y if given
        currency_locations = {}

        for currency in self.currencies.keys():
            if not self.currencies[currency]["bought"] and self.can_afford(currency):
                location = self.locate(screenshot, f"{currency}.png", 0.80, columns=self.CURRENCY_COLUMN)
                if location and (max_y is None or location[1] < max_y):
                    currency_locations[currency] = location

        # Buy any located currencies
        for currency, location in currency_locations.items():
            # Re-check since an earlier purchase this page may have spent gold
            if not self.can_afford(currency):
                continue
            buy_button_x = location[0] + self.BUY_BUTTON_COORD[0]
            buy_button_y = location[1] + self.BUY_BUTTON_COORD[1]

            # Open the buy menu, retrying until the confirmation is found
            buy_confirm = None
            while not buy_confirm:
                self.click((buy_button_x, buy_button_y), f"{currency} buy button")
                buy_confirm, screenshot = self.wait_for(f"buy_{currency}.png", 0.90, self.RETRY_TIMEOUT)

            # Handle buy confirmation, clicking again if the menu doesn't close
            while buy_confirm:
                self.click(buy_confirm, f"buy_{currency}")
                start = time()
                while buy_confirm and time() - start < self.RETRY_TIMEOUT:
                    screenshot = self.client.capture_screen()

                    insufficient_gold = self.locate(screenshot, "insufficient_gold.png", 0.90)
                    if insufficient_gold:
                        raise Exception("Insufficient Gold")

                    buy_confirm = self.locate(screenshot, f"buy_{currency}.png", 0.90)

            # After successful purchase, update currency info
            self.currencies[currency]["count"] += self.currencies[currency]["quantity"]
            if self.gold is not None:
                self.gold -= self.currencies[currency]["cost"]
            self.currencies[currency]["bought"] = True
            self.last_purchase = time()

        if self.gear or self.epic_mode != "ignore":
            self.handle_gear(screenshot, max_y)

    def find_gear(self, screenshot, max_y=None):
        # Unbought gear rows on screen as (label y, kind), top to bottom, only above max_y if given
        # kind is "gear" for non-epic, "epic_85" for level 85 epic, "epic" for lower level epic
        self.status = "Locating: equipment"
        labels = locate_all_images(screenshot, "equipment.png", 0.85, self.GEAR_LABEL_COLUMN)
        self.status = f"Locating: equipment ({len(labels)} found)"
        rows = []
        for x, y in labels:
            if max_y is not None and y >= max_y:
                continue
            button_y = y + self.GEAR_BUY_BUTTON_OFFSET

            # Skip rows whose buy button is cut off at the bottom of the screen
            if button_y + 15 > screenshot.shape[0]:
                continue

            # Skip rows that were already bought, their stock shows 0/1 instead of 1/1
            stock_region = screenshot[button_y - 20:button_y + 20, 800:880]
            if not self.locate(stock_region, "stock.png", 0.85):
                continue

            # Epic gear has a red label, level 85 epic gear is the only gear priced at 1,400,000
            hue = text_hue(screenshot, x, y, 70, 19)
            if hue is None or 15 < hue < 165:
                rows.append((y, "gear"))
            elif self.locate(screenshot[y - 8:y + 28, 820:940], "red_price.png", 0.90):
                rows.append((y, "epic_85"))
            else:
                rows.append((y, "epic"))
        return rows

    def row_snapshot(self, screenshot, label_y):
        # Icon, name and price of a row, used to recognize it again after scrolling
        return screenshot[label_y:label_y + 70, 418:930]

    def is_handled(self, screenshot, label_y):
        snapshot = self.row_snapshot(screenshot, label_y)
        for handled in self.handled_epics:
            if handled.shape == snapshot.shape and cv2.matchTemplate(handled, snapshot, cv2.TM_CCOEFF_NORMED)[0][0] > 0.95:
                return True
        return False

    def handle_gear(self, screenshot, max_y=None):
        # Deal with gear rows one at a time, rescanning after each since bought rows change
        while True:
            row = None
            for label_y, kind in self.find_gear(screenshot, max_y):
                # Only level 85 epics are paused on or bought, lower level epics are left alone
                if kind == "epic_85" and self.epic_mode != "ignore" and not self.is_handled(screenshot, label_y):
                    row = (label_y, True)
                    break
                if kind == "gear" and self.gear:
                    row = (label_y, False)
                    break
            if row is None:
                return

            label_y, epic = row
            if not epic:
                self.buy_gear(label_y)
                self.sell_gear()
                self.gear_sold += 1
            else:
                # Every epic is held down on to check it isn't boots, which are always ignored
                details = self.read_gear_details(label_y)
                self.handled_epics.append(self.row_snapshot(screenshot, label_y))
                if details is None:
                    # Never guess, let the user decide
                    self.pause("Couldn't read epic stats")
                    screenshot = self.client.capture_screen()
                    continue
                es, speed, boots = details
                if boots:
                    continue
                if self.epic_mode == "pause":
                    self.pause("Epic gear found")
                    screenshot = self.client.capture_screen()
                    continue

                # Speed is checked first, gear with a speed substat is bought whatever its ES
                if not (self.speed and speed):
                    if self.speed and self.min_es is None:
                        continue
                    if self.min_es is not None and es is None:
                        self.pause("Couldn't read epic ES")
                        screenshot = self.client.capture_screen()
                        continue
                    if self.min_es is not None and es < self.min_es:
                        continue
                self.handled_epics.pop()
                self.buy_gear(label_y)
                self.close_acquired_menu()
                self.epic_bought += 1

            screenshot = self.client.capture_screen()

    def pause(self, reason):
        # Wait until the GUI's resume button is pressed
        self.status = f"Paused: {reason}"
        self.resume_event.clear()
        self.paused = True
        self.resume_event.wait()
        self.paused = False

    def read_gear_details(self, label_y):
        # Hold down on the gear's icon to show its details, returns (equipment score, has speed, is boots)
        # None if the details never showed, the equipment score is None if it couldn't be read
        self.status = "Holding: gear icon"
        self.client.press((self.GEAR_ICON_X, label_y + self.GEAR_ICON_OFFSET))
        es_label, screenshot = self.wait_for("es_label.png", 0.90, self.RETRY_TIMEOUT)
        self.client.release()

        # Wait for the details to close before carrying on
        while self.locate(self.client.capture_screen(), "es_label.png", 0.90):
            sleep(0.1)

        if not es_label:
            return None
        # The value is right aligned at the end of the "Equipment Score" row
        x, y = es_label
        self.status = "Reading: digits"
        es = read_number(screenshot[y - 12:y + 10, x + 92:x + 157])
        self.status = "Locating: speed"
        speed = has_speed(screenshot, es_label)
        self.status = "Locating: epic_boots"
        return es, speed, is_boots(screenshot, es_label)

    def buy_gear(self, label_y):
        # Open the buy menu, retrying until the confirmation is found
        buy_confirm = None
        while not buy_confirm:
            self.click((self.GEAR_BUY_BUTTON_X, label_y + self.GEAR_BUY_BUTTON_OFFSET), "gear buy button")
            buy_confirm, _ = self.wait_for("buy_gear.png", 0.90, self.RETRY_TIMEOUT, columns=self.DIALOG_COLUMN)

        # Handle buy confirmation, clicking again if the menu doesn't close
        while buy_confirm:
            self.click(buy_confirm, "buy_gear")
            start = time()
            while buy_confirm and time() - start < self.RETRY_TIMEOUT:
                screenshot = self.client.capture_screen()

                insufficient_gold = self.locate(screenshot, "insufficient_gold.png", 0.90)
                if insufficient_gold:
                    raise Exception("Insufficient Gold")

                buy_confirm = self.locate(screenshot, "buy_gear.png", 0.90, columns=self.DIALOG_COLUMN)
        self.last_purchase = time()

    def sell_gear(self):
        # The acquired menu opens with a sell button, it slides up and ignores taps until it stops
        sell, _ = self.wait_for("sell_gear.png", 0.90, settled=True)

        # Open the sell menu, retrying until the confirmation is found
        sell_confirm = None
        while not sell_confirm:
            self.click(sell, "sell_gear")
            sell_confirm, _ = self.wait_for("sell_confirm.png", 0.90, self.RETRY_TIMEOUT)

        # Handle sell confirmation, clicking again if the menu doesn't close
        while sell_confirm:
            self.click(sell_confirm, "sell_confirm")
            start = time()
            while sell_confirm and time() - start < self.RETRY_TIMEOUT:
                screenshot = self.client.capture_screen()
                sell_confirm = self.locate(screenshot, "sell_confirm.png", 0.90)

        # Wait for the acquired menu to close before scanning the shop again
        while self.locate(screenshot, "sell_gear.png", 0.90):
            screenshot = self.client.capture_screen()

    def close_acquired_menu(self):
        # Keep the gear by tapping outside the acquired menu, retrying until it closes
        self.wait_for("sell_gear.png", 0.90)
        while True:
            self.click(self.CLOSE_MENU_COORD, "close acquired menu")
            start = time()
            while time() - start < self.RETRY_TIMEOUT:
                if not self.locate(self.client.capture_screen(), "sell_gear.png", 0.90):
                    return

    def perform_refresh(self):
        # Open the refresh menu, retrying until the confirmation is found
        refresh_confirm = None
        while not refresh_confirm:
            self.click(self.REFRESH_BUTTON_COORD, "refresh")
            refresh_confirm, _ = self.wait_for("refresh_confirm.png", 0.90, self.RETRY_TIMEOUT)

        # Handle refresh confirmation, clicking again if the menu doesn't close
        while refresh_confirm:
            self.click(refresh_confirm, "refresh_confirm")
            start = time()
            while refresh_confirm and time() - start < self.RETRY_TIMEOUT:
                screenshot = self.client.capture_screen()

                insufficient_ss = self.locate(screenshot, "insufficient_ss.png", 0.90)
                if insufficient_ss:
                    raise Exception("Insufficient Skystones")

                refresh_confirm = self.locate(screenshot, "refresh_confirm.png", 0.90)

        # Wait for the refresh to complete
        _, screenshot = self.wait_for("refresh_success.png", 0.90)

        if self.ss is not None:
            self.ss -= 3
        self.refreshes += 1
        for currency, info in self.currencies.items():
            info["bought"] = False
        self.handled_epics = []

        return screenshot

    def perform_scroll(self):
        # Scroll, retrying if the bottom of the list isn't reached
        while True:
            self.status = "Swiping: scroll down"
            self.client.scroll_down()
            scroll_success, screenshot = self.wait_for("scroll_success.png", 0.80, self.RETRY_TIMEOUT, edges=True)
            if scroll_success:
                return screenshot
