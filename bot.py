from time import sleep

from detection.image_rec import *


class Bot:
    def __init__(self, ssLimit, gLimit, bmTarget, mmTarget):
        self.ssLimit = ssLimit  # Skystone limit
        self.gLimit = gLimit  # Gold limit
        self.bmTarget = bmTarget  # Bookmark Target
        self.mmTarget = mmTarget  # Mystic Medal Target
        # self.ss, self.g = getCurrency()
        self.bm = 0
        self.mm = 0
        self.refreshes = 0

    # def getCurrency(self):
    #     return ss, g

    def handle_refresh(self, scrolled=False):
        if self.bm >= self.bmTarget and self.mm >= self.mmTarget:
            print("Obtained Desired Number of Currency")
            return

        self.buy_currency("bm", 5)
        self.buy_currency("mm", 50)

        if scrolled:
            self.perform_refresh()
            self.handle_refresh(scrolled=False)
        else:
            scroll_down()
            print("Scrolled down")
            self.handle_refresh(scrolled=True)

    def buy_currency(self, currency_type, quantity):
        image_name = f"buy_{currency_type}.png"
        currency = locate_image(f"{currency_type}.png")
        if currency:
            click_on_location((currency[0] + 415, currency[1]))
            buy_button = locate_image(image_name)
            while buy_button is None:
                sleep(1)
                buy_button = locate_image(image_name)
            click_on_location(buy_button)

            if currency_type == "bm":
                self.bm += quantity
            elif currency_type == "mm":
                self.mm += quantity

    def perform_refresh(self):
        sleep(1)
        click_on_location((162, 494))  # Refresh button location
        confirm_button = locate_image("refresh_confirm.png")
        while confirm_button is None:
            sleep(1)
            confirm_button = locate_image("refresh_confirm.png")
        click_on_location(confirm_button)
        self.refreshes += 1
        sleep(1)
