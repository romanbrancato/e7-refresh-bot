from time import sleep
from detection import *


class Bot:
    REFRESH_BUTTON_COORD = (162, 494)
    BUY_BUTTON_COORD = (415, 20)  # Values added to x and y of currency image location

    def __init__(self, client, delay, values):
        self.client = client
        self.delay = delay
        self.gold = self.gold_start = values["gold"]
        self.ss = self.ss_start = values["ss"]
        self.auto_dispatch = values["auto_dispatch"]
        self.stop_condition = values["stop_condition"]

        self.currencies = {"bm": {"quantity": 5, "cost": 184000, "count": 0, "bought": False},
                           "mm": {"quantity": 50, "cost": 280000, "count": 0, "bought": False}}
        self.refreshes = 0
        self.scrolled = False

    def handle_refresh(self):
        while self.continue_refreshing():
            self.locate_and_buy()
            self.perform_refresh() if self.scrolled else self.client.scroll_down()
            self.scrolled = not self.scrolled
            sleep(self.delay)

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
        for currency, info in self.currencies.items():
            while not info["bought"]:
                screenshot = self.client.capture_screen()
                buy_confirm = locate_image(screenshot, f"buy_{currency}.png")
                if buy_confirm:
                    while buy_confirm:
                        self.client.click(buy_confirm)
                        sleep(self.delay)
                        screenshot = self.client.capture_screen()

                        insufficient_gold = locate_image(screenshot, "insufficient_gold.png")
                        if insufficient_gold:
                            raise Exception("Insufficient Gold")

                        buy_confirm = locate_image(screenshot, f"buy_{currency}.png")

                    info["count"] += info["quantity"]
                    self.gold -= info["cost"]
                    info["bought"] = True
                    break

                currency_location = locate_image(screenshot, f"{currency}.png")
                if currency_location:
                    buy_button_x = currency_location[0] + self.BUY_BUTTON_COORD[0]
                    buy_button_y = currency_location[1] + self.BUY_BUTTON_COORD[1]
                    self.client.click((buy_button_x, buy_button_y))
                    sleep(self.delay)
                else:
                    break

    def perform_refresh(self):
        while True:
            self.client.click(self.REFRESH_BUTTON_COORD)
            sleep(self.delay)
            screenshot = self.client.capture_screen()
            refresh_confirm = locate_image(screenshot, "refresh_confirm.png")
            if refresh_confirm:
                while refresh_confirm:
                    self.client.click(refresh_confirm)
                    sleep(self.delay)
                    screenshot = self.client.capture_screen()

                    insufficient_ss = locate_image(screenshot, "insufficient_ss.png")
                    if insufficient_ss:
                        raise Exception("Insufficient Skystones")

                    refresh_confirm = locate_image(screenshot, "refresh_confirm.png")

                self.ss -= 3
                self.refreshes += 1
                for currency, info in self.currencies.items():
                    info["bought"] = False
                return
