from time import sleep

from detection import *


class Bot:
    REFRESH_BUTTON_COORD = (150, 495)
    BUY_BUTTON_COORD = (415, 20)  # Values added to x and y of currency image location

    def __init__(self, client, config):
        self.client = client
        self.delay = config["delay"]
        # Only tracked when stopping on a skystone/gold limit
        self.ss = config["ss"]
        self.gold = config["gold"]
        self.stop_condition = config["stop_condition"]

        self.currencies = {"bm": {"quantity": 5, "cost": 184000, "count": 0, "bought": False},
                           "mm": {"quantity": 50, "cost": 280000, "count": 0, "bought": False}}
        self.refreshes = 0
        self.status = "Starting"  # Current action, shown in the GUI

    def locate(self, screenshot, reference, threshold, edges=False):
        name = reference.removesuffix('.png')
        self.status = f"Locating: {name}"
        location, confidence = locate_image(screenshot, reference, threshold, edges)
        self.status = f"Locating: {name} ({confidence:.3f})"
        return location

    def click(self, point, name):
        self.status = f"Clicking: {name}"
        self.client.click(point)

    def handle_refresh(self):
        scrolled = False
        while self.continue_refreshing():
            self.locate_and_buy()
            if not scrolled:
                self.perform_scroll()
            else:
                self.perform_refresh()
            scrolled = not scrolled

    def continue_refreshing(self):
        currency = self.stop_condition["currency"]
        amount = self.stop_condition["amount"]

        if currency == "ss":
            # Only refresh if it won't drop skystones below the limit
            return self.ss - 3 >= amount

        if currency == "gold":
            # Only refresh if there's enough gold above the limit to buy something
            return self.gold - min(info["cost"] for info in self.currencies.values()) >= amount

        return amount == 0 or self.currencies[currency]["count"] < amount

    def can_afford(self, currency):
        # Skip purchases that would drop gold below the limit
        if self.gold is None:
            return True
        return self.gold - self.currencies[currency]["cost"] >= self.stop_condition["amount"]

    def locate_and_buy(self):
        # Locate all available currencies
        screenshot = self.client.capture_screen()
        currency_locations = {}

        for currency in self.currencies.keys():
            if not self.currencies[currency]["bought"] and self.can_afford(currency):
                location = self.locate(screenshot, f"{currency}.png", 0.80)
                if location:
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
                sleep(self.delay)
                screenshot = self.client.capture_screen()
                buy_confirm = self.locate(screenshot, f"buy_{currency}.png", 0.90)

            # Handle buy confirmation
            while buy_confirm:
                self.click(buy_confirm, f"buy_{currency}")
                sleep(self.delay)
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

        # Check for red gear
        if self.stop_condition["red_gear"]:
            red_gear = self.locate(screenshot, f"red_gear.png", 0.97)
            red_price = self.locate(screenshot, f"red_price.png", 0.97)
            if red_gear or red_price:
                raise Exception("Red Gear Located")

    def perform_refresh(self):
        while True:
            self.click(self.REFRESH_BUTTON_COORD, "refresh")
            sleep(self.delay)
            screenshot = self.client.capture_screen()
            refresh_confirm = self.locate(screenshot, "refresh_confirm.png", 0.90)
            if refresh_confirm:
                while refresh_confirm:
                    self.click(refresh_confirm, "refresh_confirm")
                    sleep(self.delay)
                    screenshot = self.client.capture_screen()

                    insufficient_ss = self.locate(screenshot, "insufficient_ss.png", 0.90)
                    if insufficient_ss:
                        raise Exception("Insufficient Skystones")

                    refresh_confirm = self.locate(screenshot, "refresh_confirm.png", 0.90)

                # Wait for the refresh to complete
                refresh_success = None
                while not refresh_success:
                    sleep(0.1)
                    screenshot = self.client.capture_screen()
                    refresh_success = self.locate(screenshot, "refresh_success.png", 0.90)

                if self.ss is not None:
                    self.ss -= 3
                self.refreshes += 1
                for currency, info in self.currencies.items():
                    info["bought"] = False
                return

    def perform_scroll(self):
        multiplier = 2
        while True:
            self.status = "Scrolling"
            self.client.scroll_down()
            sleep(self.delay * multiplier)
            screenshot = self.client.capture_screen()
            scroll_success = self.locate(screenshot, "scroll_success.png", 0.80, edges=True)
            if scroll_success:
                return
            multiplier += 1
