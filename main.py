from bot import Bot
from detection.image_rec import *


def main():
    bot = Bot(0,0,5,50)
    bot.handle_refresh()

if __name__ == '__main__':
    main()
