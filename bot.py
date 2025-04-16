from time import sleep

from detection import *


class Bot:
    REFRESH_BUTTON_COORD = (150, 495)
    BUY_BUTTON_COORD = (415, 20)  # Values added to x and y of currency image location

    def __init__(self, client, config):
        self.client = client
        self.delay = config["delay"]
        self.gold = config["gold"]
        self.ss = config["ss"]
        self.stop_condition = config["stop_condition"]

        self.currencies = {"bm": {"quantity": 5, "cost": 184000, "count": 0, "bought": False},
                           "mm": {"quantity": 50, "cost": 280000, "count": 0, "bought": False}}
        self.refreshes = 0

    def handle_refresh(self):
        scrolled = False
        while self.continue_refreshing():
            self.locate_and_buy()
            if not scrolled:
                self.client.scroll_down()
                sleep(self.delay * 2)
            else:
                self.perform_refresh()
            scrolled = not scrolled

    def continue_refreshing(self):
        if self.gold >= 184000 and self.ss >= 3:
            if (self.stop_condition["amount"] == 0 or
                    (self.stop_condition["currency"] in {"mm", "bm"} and
                     self.currencies[self.stop_condition["currency"]]["count"] < self.stop_condition["amount"]) or
                    (self.stop_condition["currency"] == "ss" and self.ss > self.stop_condition["amount"])
            ):
                return True
            else:
                return False
        else:
            raise Exception("Low Gold" if self.gold < 184000 else "Low Skystones")

    def locate_and_buy(self):
        # Locate all available currencies
        screenshot = self.client.capture_screen()
        currency_locations = {}

        for currency in self.currencies.keys():
            if not self.currencies[currency]["bought"]:
                location = locate_image(screenshot, f"{currency}.png", 0.80)
                if location:
                    currency_locations[currency] = location

        # Buy any located currencies
        for currency, location in currency_locations.items():
            while True:
                buy_button_x = location[0] + self.BUY_BUTTON_COORD[0]
                buy_button_y = location[1] + self.BUY_BUTTON_COORD[1]
                self.client.click((buy_button_x, buy_button_y))
                sleep(self.delay)

                # Handle buy confirmation
                screenshot = self.client.capture_screen()
                buy_confirm = locate_image(screenshot, f"buy_{currency}.png", 0.90)

                while buy_confirm:
                    self.client.click(buy_confirm)
                    sleep(self.delay)
                    screenshot = self.client.capture_screen()

                    insufficient_gold = locate_image(screenshot, "insufficient_gold.png", 0.90)
                    if insufficient_gold:
                        raise Exception("Insufficient Gold")

                    buy_confirm = locate_image(screenshot, f"buy_{currency}.png", 0.90)

                # After successful purchase, update currency info
                self.currencies[currency]["count"] += self.currencies[currency]["quantity"]
                self.gold -= self.currencies[currency]["cost"]
                self.currencies[currency]["bought"] = True
                break

        # Check for red gear
        if self.stop_condition["red_gear"]:
            red_gear = locate_image(screenshot, f"red_gear.png", 0.97)
            red_price = locate_image(screenshot, f"red_price.png", 0.97)
            if red_gear or red_price:
                raise Exception("Red Gear Located")

    def perform_refresh(self):
        while True:
            self.client.click(self.REFRESH_BUTTON_COORD)
            sleep(self.delay)
            screenshot = self.client.capture_screen()
            refresh_confirm = locate_image(screenshot, "refresh_confirm.png", 0.90)
            if refresh_confirm:
                while refresh_confirm:
                    self.client.click(refresh_confirm)
                    sleep(self.delay)
                    screenshot = self.client.capture_screen()

                    insufficient_ss = locate_image(screenshot, "insufficient_ss.png", 0.90)
                    if insufficient_ss:
                        raise Exception("Insufficient Skystones")

                    refresh_confirm = locate_image(screenshot, "refresh_confirm.png", 0.90)

                # Wait for the refresh to complete
                sleep(self.delay * 2)
                screenshot = self.client.capture_screen()
                refresh_success = locate_image(screenshot, "refresh_success.png", 0.90)
                while not refresh_success:
                    sleep(0.1)
                    screenshot = self.client.capture_screen()
                    refresh_success = locate_image(screenshot, "refresh_success.png", 0.90)

                self.ss -= 3
                self.refreshes += 1
                for currency, info in self.currencies.items():
                    info["bought"] = False
                return
