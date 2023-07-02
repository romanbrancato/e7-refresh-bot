from time import sleep

from detection.image_rec import *


class Bot:
    def __init__(self, client, g, ss, g_limit, ss_limit, bm_target, mm_target):
        self.client = client  # Emulator instance
        self.g = g  # Current gold
        self.ss = ss  # Current skystones
        self.gLimit = g_limit  # Gold limit
        self.ssLimit = ss_limit  # Skystone limit
        self.bmTarget = bm_target  # Bookmark target
        self.mmTarget = mm_target  # Mystic medal target

        self.bm = 0  # Number of bookmarks acquired
        self.mm = 0  # Number of mystic medals acquired
        self.refreshes = 0  # Number of refreshes done
        self.bought_currencies = {"bm": False, "mm": False}  # Track bought currencies

    def can_refresh(self):
        if self.bm < self.bmTarget or self.mm < self.mmTarget:
            if self.g > self.gLimit and self.ss > self.ssLimit:
                return True
            else:
                print("Currency Limit Reached")
                return False
        else:
            print("Obtained Desired Number of Currency")
            return False

    def handle_refresh(self, scrolled=False):
        if self.can_refresh():
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
        currency = locate_image(f"{currency_type}.png", self.client.index)
        if currency:
            self.client.click_on_location(
                (currency[0] + 415, currency[1] + 20))  # Location of buy button relative to bm/mm image
            buy_button = locate_image(image_name, self.client.index)
            counter = 0

            while buy_button is None and counter < attempts:
                sleep(1)
                self.client.capture_screen()
                buy_button = locate_image(image_name, self.client.index)
                counter += 1

            if buy_button is None:
                # Maximum attempts reached, retry
                print("Retrying Buying Currency")
                self.buy_currency(currency_type, quantity, attempts)
            else:
                self.client.click_on_location(buy_button)
                self.g -= 184000 if currency_type == "bm" else 280000  # Subtract currency amount after purchase
                sleep(1)

                if currency_type == "bm":
                    self.bm += quantity
                elif currency_type == "mm":
                    self.mm += quantity

                self.bought_currencies[currency_type] = True

    def perform_refresh(self, attempts=3):
        self.client.click_on_location((162, 494))  # Refresh button location
        self.client.capture_screen()
        confirm_button = locate_image("refresh_confirm.png", self.client.index)
        counter = 0

        while confirm_button is None and counter < attempts:
            sleep(1)
            self.client.capture_screen()
            confirm_button = locate_image("refresh_confirm.png", self.client.index)
            counter += 1

        if confirm_button is None:
            # Maximum attempts reached, retry
            print("Retrying Refresh")
            self.perform_refresh(attempts)
        else:
            self.client.click_on_location(confirm_button)
            self.refreshes += 1
            self.ss -= 3
            self.bought_currencies = {"bm": False, "mm": False}  # Reset bought currencies
            sleep(1)
