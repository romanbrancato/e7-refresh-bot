from time import sleep
from detection import *


class Bot:
    REFRESH_BUTTON_COORD = (162, 494)
    BUY_BUTTON_COORD = (415, 20)  # Values added to x and y of currency image location
    DELAY = 0.3

    def __init__(self, client, values):
        self.client = client
        self.gold = values["gold"]
        self.ss = values["ss"]
        self.auto_dispatch = values["auto_dispatch"]
        self.bookmark_target = values["bm_target"]
        self.mystic_medal_target = values["mm_target"]
        self.ss_limit = values["ss_limit"]
        self.selected_option = values["selected_option"]
        self.log_callback = None

        self.currencies = {"bm": {"quantity": 5, "count": 0, "bought": False},
                           "mm": {"quantity": 50, "count": 0, "bought": False}}
        self.refreshes = 0
        self.scrolled = False

    def handle_refresh(self):
        while self.continue_refreshing():
            self.locate_and_buy()
            self.perform_refresh() if self.scrolled else self.client.scroll_down()
            self.scrolled = not self.scrolled
            sleep(self.DELAY)

    def continue_refreshing(self):
        if self.bookmark_target == self.mystic_medal_target == 0:
            return True
        elif any(self.currencies[c]["count"] < target for c, target in
                 [("bm", self.bookmark_target), ("mm", self.mystic_medal_target)]):
            return True
        else:
            print("Obtained Desired Number of Currency")
            return False

    def locate_and_buy(self):
        for currency, info in self.currencies.items():
            while not info["bought"]:
                buy_confirm = locate_image(self.client.capture_screen(), f"buy_{currency}.png")
                if buy_confirm:
                    while buy_confirm:
                        self.client.click(buy_confirm)
                        sleep(self.DELAY)

                        insufficient_gold = locate_image(self.client.capture_screen(), "insufficient_gold.png")
                        if insufficient_gold:
                            raise Exception("Insufficient Gold")

                        buy_confirm = locate_image(self.client.capture_screen(), f"buy_{currency}.png")

                    info["count"] += info["quantity"]
                    info["bought"] = True
                    self.log_callback()
                    break

                currency_location = locate_image(self.client.capture_screen(), f"{currency}.png")
                if currency_location:
                    buy_button_x = currency_location[0] + self.BUY_BUTTON_COORD[0]
                    buy_button_y = currency_location[1] + self.BUY_BUTTON_COORD[1]
                    self.client.click((buy_button_x, buy_button_y))
                    sleep(self.DELAY)
                else:
                    break

    def perform_refresh(self):
        while True:
            self.client.click(self.REFRESH_BUTTON_COORD)
            sleep(self.DELAY)
            refresh_confirm = locate_image(self.client.capture_screen(), "refresh_confirm.png")
            if refresh_confirm:
                while refresh_confirm:
                    self.client.click(refresh_confirm)
                    sleep(self.DELAY)

                    insufficient_ss = locate_image(self.client.capture_screen(), "insufficient_ss.png")
                    if insufficient_ss:
                        raise Exception("Insufficient Skystones")

                    refresh_confirm = locate_image(self.client.capture_screen(), "refresh_confirm.png")

                self.refreshes += 1
                self.log_callback()
                for currency, info in self.currencies.items():
                    info["bought"] = False
                return