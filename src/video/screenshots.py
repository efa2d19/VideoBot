from pyppeteer import launch
from pyppeteer.errors import TimeoutError as BrowserTimeoutError

from os import getenv

from typing import TypeVar, Optional, Union, Callable


_function = TypeVar('_function', bound=Callable[..., object])
_exceptions = TypeVar('_exceptions', bound=Optional[Union[str, tuple, list]])


class ExceptionDecorator:
    __default_exception = BrowserTimeoutError

    def __init__(
            self,
            exception: '_exceptions' = None,
    ):
        if exception:
            self.__exception = exception
        else:
            self.__exception = self.__default_exception

    def __call__(
            self,
            func,
    ):
        async def wrapper(*args, **kwargs):
            try:
                obj_to_return = await func(*args, **kwargs)
                return obj_to_return
            except Exception as caughtException:
                if type(self.__exception) == type:
                    if caughtException == self.__exception:
                        print('expected', caughtException)
                    else:
                        print('unexpected', caughtException)
                else:
                    if caughtException in self.__exception:
                        print('expected', caughtException)
                    else:
                        print('unexpected', caughtException)

        return wrapper


def catch_exception(
        func: Optional[_function],
        exception: Optional[_exceptions] = None,
) -> ExceptionDecorator | _function:
    exceptor = ExceptionDecorator(exception=exception)
    if func:
        exceptor = exceptor(func)
    return exceptor


# It exists, so I can import everything at once
# And to add it to other classes for other socials
class Browser:
    default_Viewport = dict()
    default_Viewport['width'] = 1920
    default_Viewport['height'] = 1080
    default_Viewport['isLandscape'] = True

    async def get_browser(
            self,
    ):
        return await launch(self.default_Viewport)

    @staticmethod
    async def close_browser(
            browser: 'launch',
    ) -> None:
        await browser.close()


class Wait:

    @staticmethod
    async def find_xpath(
            page,
            xpath: str,
    ):
        el = await page.waitForXPath(xpath)
        return el

    @catch_exception
    async def click(
            self,
            page,
            xpath: str,
    ) -> None:
        el = await self.find_xpath(page, xpath)
        await el.click()

    @catch_exception
    async def screenshot(
            self,
            page,
            xpath: str,
            options: dict,
    ) -> None:
        el = await self.find_xpath(page, xpath)
        await el.screenshot(options)


class RedditScreenshot(Browser, Wait):
    __dark_mode = getenv('dark_theme', 'True') if getenv('dark_theme', 'True') else 'True'

    async def dark_theme(
            self,
            page: 'launch',
    ) -> None:
        if self.__dark_mode == 'True':

            await self.click(page, '//*[contains(@class, \'header-user-dropdown\')]')

            await self.click(page, '//*[contains(text(), \'Settings\')]/ancestor::button[1]')

            await self.click(page, '//*[contains(text(), \'Dark Mode\')]/ancestor::button[1]')

            # Closes settings
            await self.click(page, '//*[contains(@class, \'header-user-dropdown\')]')

    async def __call__(
            self,
            browser,
            link: str,
            el_class: str,
            filename: str | int,
            is_nsfw: bool,
    ) -> None:
        reddit_main = await browser.newPage()
        await reddit_main.goto(link)

        await self.dark_theme(reddit_main)

        if is_nsfw:
            await self.click(
                reddit_main,
                '//*[contains(text(), \'Click to see nsfw\')]'
            )
            await self.click(
                reddit_main,
                '//*[contains(text(), \'Yes\')]'
            )

        await self.screenshot(
            reddit_main,
            f'//*[contains(@id, \'{el_class}\')]',
            {'path': f'assets/img/{filename}.png'}
        )
