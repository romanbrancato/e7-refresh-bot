from time import sleep

from detection.image_rec import *


class Bot:
    BOOKMARK_COST = 184000
    MYSTIC_MEDAL_COST = 280000

    def __init__(self, client, current_gold, gold_limit, current_skystones, skystone_limit, bookmark_target, mystic_medal_target):
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

    def handle_refresh(self, scrolled=False):
        if self.can_refresh() and self.refreshing:
            if not self.bought_currencies["bm"]:
                self.buy_currency("bm", 5)
            if not self.bought_currencies["mm"]:
                self.buy_currency("mm", 50)

            if scrolled:
                self.perform_refresh()
                self.handle_refresh(scrolled=False)
            else:
                self.client.scroll_down()
                print("Scrolled down")
                self.handle_refresh(scrolled=True)

    def buy_currency(self, currency_type, quantity, attempts=3):

        image_name = f"buy_{currency_type}.png"
        self.client.capture_screen()
        currency = locate_image(f"{currency_type}.png", self.client.emulator_index)
        if currency:
            self.client.click_on_location(
                (currency[0] + 415, currency[1] + 20))  # Location of buy button relative to bm/mm image
            buy_button = locate_image(image_name, self.client.emulator_index)
            counter = 0

            while buy_button is None and counter < attempts:
                sleep(1)
                self.client.capture_screen()
                buy_button = locate_image(image_name, self.client.emulator_index)
                counter += 1

            if buy_button is None:
                # Maximum attempts reached, retry
                print("Retrying Buying Currency")
                self.buy_currency(currency_type, quantity, attempts)
            else:
                self.client.click_on_location(buy_button)
                self.current_gold -= self.BOOKMARK_COST if currency_type == "bm" else self.MYSTIC_MEDAL_COST
                sleep(1)

                if currency_type == "bm":
                    self.bookmarks += quantity
                elif currency_type == "mm":
                    self.mystic_medals += quantity

                self.bought_currencies[currency_type] = True

    def perform_refresh(self, attempts=3):
        self.client.click_on_location((162, 494))  # Refresh button location
        self.client.capture_screen()
        confirm_button = locate_image("refresh_confirm.png", self.client.emulator_index)
        counter = 0

        while confirm_button is None and counter < attempts:
            sleep(1)
            self.client.capture_screen()
            confirm_button = locate_image("refresh_confirm.png", self.client.emulator_index)
            counter += 1

        if confirm_button is None:
            # Maximum attempts reached, retry
            print("Retrying Refresh")
            self.perform_refresh(attempts)
        else:
            self.client.click_on_location(confirm_button)
            self.refreshes += 1
            self.current_skystones -= 3
            self.bought_currencies = {"bm": False, "mm": False}  # Reset bought currencies
            sleep(1)
