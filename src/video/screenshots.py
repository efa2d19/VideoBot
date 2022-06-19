from pyppeteer import launch
from pyppeteer.page import Page as PageCls
from pyppeteer.browser import Browser as BrowserCls
from pyppeteer.errors import TimeoutError as BrowserTimeoutError

from os import getenv

from typing import TypeVar, Optional, Union, Callable, Coroutine


_function = TypeVar('_function', bound=Callable[..., object])
_exceptions = TypeVar('_exceptions', bound=Optional[Union[str, tuple, list]])


class ExceptionDecorator:
    __default_exception = BrowserTimeoutError  # TODO it's something else, always triggers unexpected

    def __init__(
            self,
            exception: Optional[_exceptions] = None,
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
            except Exception as caughtException:  # TODO add .log file for errors
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
    default_Viewport['isLandscape'] = True

    async def get_browser(
            self,
    ) -> 'BrowserCls':
        return await launch(self.default_Viewport)

    @staticmethod
    async def close_browser(
            browser: BrowserCls,
    ) -> None:
        await browser.close()


class Wait:

    @staticmethod
    @catch_exception
    async def find_xpath(
            page_instance: PageCls,
            xpath: Optional[str] = None,
            options: Optional[dict] = None,
    ):
        if options:
            el = await page_instance.waitForXPath(xpath, options=options)
        else:
            el = await page_instance.waitForXPath(xpath)
        return el

    @catch_exception
    async def click(
            self,
            page_instance: Optional[PageCls] = None,
            xpath: Optional[str] = None,
            find_options: Optional[dict] = None,
            el: Optional[Coroutine] = None,
    ) -> None:
        if not el:
            el = await self.find_xpath(page_instance, xpath, find_options)
        await el.click()

    @catch_exception
    async def screenshot(
            self,
            page_instance: Optional[PageCls] = None,
            xpath: Optional[str] = None,
            options: Optional[dict] = None,
            find_options: Optional[dict] = None,
            el: Optional[Coroutine] = None,
    ) -> None:
        if options is None:
            options = {}
        if not el:
            el = await self.find_xpath(page_instance, xpath, find_options)
        await el.screenshot(options)


class RedditScreenshot(Browser, Wait):
    __dark_mode = getenv('dark_theme', 'True') if getenv('dark_theme', 'True') else 'True'

    async def dark_theme(  # TODO
            self,
            page_instance: Optional[PageCls] = None,
    ) -> None:
        if self.__dark_mode == 'True':

            await self.click(
                page_instance, 
                '//*[contains(@class, \'header-user-dropdown\')]',
                {'timeout': 5000},
            )

            # It's normal not to find it, sometimes there is none :shrug:
            await self.click(
                page_instance,
                '//*[contains(text(), \'Settings\')]/ancestor::button[1]',
                {'timeout': 5000},
            )

            await self.click(
                page_instance,
                '//*[contains(text(), \'Dark Mode\')]/ancestor::button[1]',
                {'timeout': 5000},
            )

            # Closes settings
            await self.click(
                page_instance,
                '//*[contains(@class, \'header-user-dropdown\')]',
                {'timeout': 5000},
            )

    async def __call__(
            self,
            browser: 'BrowserCls',
            link: str,
            el_class: str,
            filename: str | int,
            is_nsfw: bool,
    ) -> None:
        reddit_main = await browser.newPage()
        await reddit_main.goto(link)

        await self.dark_theme(reddit_main)

        if is_nsfw:  # TODO test it, works bad, no elements
            await self.click(
                reddit_main,
                '//*[contains(text(), \'Click to see nsfw\')]',
                {'timeout': 5000},
            )
            await self.click(
                reddit_main,
                '//*[contains(text(), \'Yes\')]',
                {'timeout': 5000},
            )

        await self.screenshot(
            reddit_main,
            f'//*[contains(@id, \'{el_class}\')]',
            {'path': f'assets/img/{filename}.png'},
        )
