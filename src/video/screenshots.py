from pyppeteer import launch
from pyppeteer.errors import TimeoutError as BrowserTimeoutError

from os import getenv


# It exists, so I can import everything at once
# And to add it to other classes for other socials
class Browser:
    default_Viewport = dict()
    default_Viewport['width'] = 1920
    default_Viewport['height'] = 1080
    default_Viewport['isLandscape'] = True

    async def get_browser(
            self,
    ) -> 'launch':
        return await launch(self.default_Viewport)

    @staticmethod
    async def close_browser(
            browser: 'launch',
    ) -> None:
        await browser.close()


class RedditScreenshot(Browser):
    __dark_mode_enabled = False

    @staticmethod
    async def dark_theme(
            page: 'launch',
    ) -> None:
        if getenv('dark_theme', 'True') == 'True':
            el = await page.waitForXPath('//*[contains(@class, \'header-user-dropdown\')]')
            await el.click()
            try:
                el = await page.waitForXPath('//*[contains(text(), \'Settings\')]/ancestor::button[1]')
                await el.click()
            except BrowserTimeoutError:  # Sometimes there's no Settings (lol idk)
                pass
            el = await page.waitForXPath('//*[contains(text(), \'Dark Mode\')]/ancestor::button[1]')
            await el.click()

    async def __call__(
            self,
            browser: 'launch',
            link: str,
            el_class: str,
            filename: str | int,
            is_nsfw: bool,
    ) -> None:
        reddit_main = await browser.newPage()
        await reddit_main.goto(link)

        await self.dark_theme(reddit_main)

        if is_nsfw:
            try:  # Closes nsfw warning if there is one
                el = await reddit_main.waitForXPath('//*[contains(text(), \'Click to see nsfw\')]')
                await el.click()
            except BrowserTimeoutError:
                try:  # Closes nsfw warning if there is one
                    el = await reddit_main.waitForXPath('//*[contains(text(), \'Yes\')]')
                    await el.click()
                except BrowserTimeoutError:
                    pass

        el = await reddit_main.waitForXPath(f'//*[contains(@id, \'{el_class}\')]')
        await el.screenshot({'path': f'assets/img/{filename}.png'})
