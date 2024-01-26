from time import sleep
from detection.image_rec import *


class Bot:
    REFRESH_BUTTON_COORD = (162, 494)
    BUY_BUTTON_COORD = (415, 20)  # Values added to the x and y-axis
    DELAY = 0.3

    def __init__(self, client, bookmark_target, mystic_medal_target):
        self.client = client
        self.bookmark_target = bookmark_target
        self.mystic_medal_target = mystic_medal_target

        self.currencies = {"bm": {"quantity": 5, "count": 0, "bought": False},
                           "mm": {"quantity": 50, "count": 0, "bought": False}}
        self.refreshes = 0
        self.scrolled = False
        self.refreshing = False

    def continue_refreshing(self):
        if self.bookmark_target == self.mystic_medal_target == 0:
            return True
        elif any(self.currencies[c]["count"] < target for c, target in
                 [("bm", self.bookmark_target), ("mm", self.mystic_medal_target)]):
            return True
        else:
            print("Obtained Desired Number of Currency")
            return False

    def handle_refresh(self):
        while self.continue_refreshing() and self.refreshing:
            self.locate_and_buy()
            if self.refreshing:
                self.perform_refresh() if self.scrolled else self.client.scroll_down()
                self.scrolled = not self.scrolled
                sleep(self.DELAY)
        self.refreshing = False

    def locate_and_buy(self):
        for currency, info in self.currencies.items():
            while not info["bought"] and self.refreshing:
                self.client.capture_screen()
                buy_confirm = locate_image(f"buy_{currency}.png", self.client.emulator_index)
                if buy_confirm:
                    while buy_confirm and self.refreshing:
                        self.client.click(buy_confirm)
                        sleep(self.DELAY)
                        self.client.capture_screen()

                        insufficient_gold = locate_image("insufficient_gold.png", self.client.emulator_index)
                        if insufficient_gold:
                            print("Insufficient Gold, Cannot Buy Currency")
                            self.refreshing = False
                            return

                        buy_confirm = locate_image(f"buy_{currency}.png", self.client.emulator_index)

                    info["count"] += info["quantity"]
                    info["bought"] = True
                    break

                currency_location = locate_image(f"{currency}.png", self.client.emulator_index)
                if currency_location:
                    buy_button_x = currency_location[0] + self.BUY_BUTTON_COORD[0]
                    buy_button_y = currency_location[1] + self.BUY_BUTTON_COORD[1]
                    self.client.click((buy_button_x, buy_button_y))
                    sleep(self.DELAY)
                else:
                    break

    def perform_refresh(self):
        while self.refreshing:
            refresh_confirm = locate_image("refresh_confirm.png", self.client.emulator_index)
            if refresh_confirm:
                while refresh_confirm and self.refreshing:
                    self.client.click(refresh_confirm)
                    sleep(self.DELAY)
                    self.client.capture_screen()

                    insufficient_ss = locate_image("insufficient_ss.png", self.client.emulator_index)
                    if insufficient_ss:
                        print("Insufficient Skystones, Cannot Refresh")
                        self.refreshing = False
                        return

                    refresh_confirm = locate_image("refresh_confirm.png", self.client.emulator_index)

                self.refreshes += 1
                for currency, info in self.currencies.items():
                    info["bought"] = False
                return

            self.client.click(self.REFRESH_BUTTON_COORD)
            sleep(self.DELAY)
            self.client.capture_screen()
