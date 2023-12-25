from time import sleep

from detection.image_rec import *


class Bot:
    REFRESH_COST = 3
    REFRESH_BUTTON_COORD = (162, 494)
    BUY_BUTTON_COORD = (415, 20)  # Values added to the x and y-axis

    def __init__(self, client, bookmark_target, mystic_medal_target):
        self.client = client
        self.bookmark_target = bookmark_target
        self.mystic_medal_target = mystic_medal_target

        self.bought_currencies = {"bm": False, "mm": False}
        self.bookmarks = 0
        self.mystic_medals = 0
        self.refreshes = 0
        self.scrolled = False
        self.refreshing = False

    def can_refresh(self):
        # Check for insufficient currency pop-ups before this

        if self.bookmark_target == 0 and self.mystic_medal_target == 0:
            return True
        elif self.bookmarks < self.bookmark_target or self.mystic_medals < self.mystic_medal_target:
            return True
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
            # Image Detection can be too fast resulting in bad coordinates for buy button
            tries_before_recalculate = 3
            tries = 0

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
                    tries += 1
                    if tries >= tries_before_recalculate:
                        # Recalculate the currency position
                        self.client.capture_screen()
                        currency = locate_image(f"{currency_type}.png", self.client.emulator_index)
                        tries = 0

            while buy_confirm:
                self.client.click_on_location(buy_confirm)
                sleep(0.3)
                # Check if currency has successfully been bought
                self.client.capture_screen()
                buy_confirm = locate_image(image_name, self.client.emulator_index)

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
        self.bought_currencies = {"bm": False, "mm": False}  # Reset bought currencies
