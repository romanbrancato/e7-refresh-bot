from time import sleep

from detection.image_rec import *


class Bot:
    BOOKMARK_COST = 184000
    MYSTIC_MEDAL_COST = 280000
    REFRESH_COST = 3
    REFRESH_BUTTON_COORD = (162, 494)
    BUY_BUTTON_COORD = (415, 20)  # Values added to the x and y-axis

    def __init__(self, client, current_gold, gold_limit, current_skystones, skystone_limit, bookmark_target,
                 mystic_medal_target):
        self.client = client  # Emulator instance
        self.current_gold = current_gold
        self.gold_limit = gold_limit
        self.current_skystones = current_skystones
        self.skystone_limit = skystone_limit
        self.bookmark_target = bookmark_target
        self.mystic_medal_target = mystic_medal_target

        self.bought_currencies = {"bm": False, "mm": False}  # Track bought currencies

        self.bookmarks = 0  # Number of bookmarks acquired
        self.mystic_medals = 0  # Number of mystic medals acquired
        self.refreshes = 0
        self.scrolled = False  # Track scroll state
        self.refreshing = False  # Track bot operation status

    def can_refresh(self):
        if self.bookmarks < self.bookmark_target or self.mystic_medals < self.mystic_medal_target:
            if self.current_gold > self.gold_limit and self.current_skystones > self.skystone_limit:
                return True
            else:
                print("Currency Limit Reached")
                return False
        else:
            print("Obtained Desired Number of Currency")
            return False

    def handle_refresh(self):
        while self.refreshing:
            if self.can_refresh():
                sleep(0.3)
                if not self.bought_currencies["bm"]:
                    self.buy_currency("bm", 5)
                if not self.bought_currencies["mm"]:
                    self.buy_currency("mm", 50)

                if self.scrolled:
                    self.perform_refresh()
                else:
                    self.client.scroll_down()
                    print("scrolled down")
                self.scrolled = not self.scrolled
            else:
                self.refreshing = False

    def buy_currency(self, currency_type, quantity):
        image_name = f"buy_{currency_type}.png"
        self.client.capture_screen()
        currency = locate_image(f"{currency_type}.png", self.client.emulator_index)

        if currency:
            max_tries_before_recalculate = 3
            try_count = 0

            while True:
                # Calculate the buy button coordinates relative to the currency's position
                buy_button_x = currency[0] + self.BUY_BUTTON_COORD[0]
                buy_button_y = currency[1] + self.BUY_BUTTON_COORD[1]

                self.client.click_on_location((buy_button_x, buy_button_y))
                sleep(0.3)
                self.client.capture_screen()
                buy_confirm = locate_image(image_name, self.client.emulator_index)

                if buy_confirm:
                    break
                else:
                    try_count += 1
                    if try_count >= max_tries_before_recalculate:
                        # Recalculate the currency position
                        self.client.capture_screen()
                        currency = locate_image(f"{currency_type}.png", self.client.emulator_index)
                        try_count = 0

            while buy_confirm:
                self.client.click_on_location(buy_confirm)
                sleep(0.3)
                # Check if currency has successfully been bought
                self.client.capture_screen()
                buy_confirm = locate_image(image_name, self.client.emulator_index)

            self.current_gold -= self.BOOKMARK_COST if currency_type == "bm" else self.MYSTIC_MEDAL_COST

            if currency_type == "bm":
                self.bookmarks += quantity
            elif currency_type == "mm":
                self.mystic_medals += quantity

            self.bought_currencies[currency_type] = True

    def perform_refresh(self):
        while True:
            self.client.click_on_location(self.REFRESH_BUTTON_COORD)
            sleep(0.3)
            # Check if refresh has been performed
            self.client.capture_screen()
            refresh_confirm = locate_image("refresh_confirm.png", self.client.emulator_index)
            if refresh_confirm:
                break

        while refresh_confirm:
            self.client.click_on_location(refresh_confirm)
            sleep(0.3)
            # Check if refresh has been performed
            self.client.capture_screen()
            refresh_confirm = locate_image("refresh_confirm.png", self.client.emulator_index)

        self.refreshes += 1
        self.current_skystones -= self.REFRESH_COST
        self.bought_currencies = {"bm": False, "mm": False}  # Reset bought currencies
