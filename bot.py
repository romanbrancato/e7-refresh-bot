from time import sleep

from detection.image_rec import *


class Bot:
    REFRESH_COST = 3
    REFRESH_BUTTON_COORD = (162, 494)
    BUY_BUTTON_COORD = (415, 20)  # Values added to the x and y-axis
    DELAY = 0.3

    def __init__(self, client, bookmark_target, mystic_medal_target):
        self.client = client
        self.bookmark_target = bookmark_target
        self.mystic_medal_target = mystic_medal_target

        self.currencies = {"bm": {"quantity": 5, "count": 0, "bought": False},
                           "mm": {"quantity": 5, "count": 0, "bought": False}}
        self.refreshes = 0
        self.scrolled = False
        self.refreshing = False

    def continue_refreshing(self):
        if self.bookmark_target == 0 and self.mystic_medal_target == 0:
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
        self.client.capture_screen()

        for currency in self.currencies:
            if not self.currencies[currency]["bought"]:
                currency_location = locate_image(f"{currency}.png", self.client.emulator_index)

                if currency_location:
                    buy_confirm = None

                    while not buy_confirm:
                        currency_location = locate_image(f"{currency}.png", self.client.emulator_index)
                        # Calculate the buy button coordinates relative to the currency's position
                        buy_button_x, buy_button_y = currency_location[0] + self.BUY_BUTTON_COORD[0], currency_location[
                            1] + self.BUY_BUTTON_COORD[1]
                        self.client.click_on_location((buy_button_x, buy_button_y))
                        sleep(self.DELAY)
                        self.client.capture_screen()
                        buy_confirm = locate_image(f"buy_{currency}.png", self.client.emulator_index)

                    while buy_confirm:
                        self.client.click_on_location(buy_confirm)
                        sleep(self.DELAY)
                        # Check if insufficient gold or currency has successfully been bought
                        self.client.capture_screen()
                        insufficient_gold = locate_image("insufficient_gold.png", self.client.emulator_index)
                        if insufficient_gold:
                            print("Insufficient Gold, Cannot Buy Currency")
                            self.refreshing = False
                            return
                        buy_confirm = locate_image(f"buy_{currency}.png", self.client.emulator_index)
                        self.currencies[currency]["count"] += self.currencies[currency]["quantity"]

                    self.currencies[currency]["bought"] = True

    def perform_refresh(self):
        refresh_confirm = None

        while not refresh_confirm:
            self.client.click_on_location(self.REFRESH_BUTTON_COORD)
            sleep(self.DELAY)
            self.client.capture_screen()
            refresh_confirm = locate_image("refresh_confirm.png", self.client.emulator_index)

        while refresh_confirm:
            self.client.click_on_location(refresh_confirm)
            sleep(self.DELAY)
            self.client.capture_screen()
            # insufficient_ss = locate_image("insufficient_ss.png", self.client.emulator_index)
            # if insufficient_ss:
            #     print("Insufficient Skystones, Cannot Refresh")
            #     self.refreshing = False
            #     return
            refresh_confirm = locate_image("refresh_confirm.png", self.client.emulator_index)

        self.refreshes += 1

        for currency in self.currencies:
            self.currencies[currency]["bought"] = False
