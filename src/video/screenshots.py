from pyppeteer import launch
from pyppeteer.page import Page as PageCls
from pyppeteer.element_handle import ElementHandle as ElementHandleCls
from pyppeteer.browser import Browser as BrowserCls
from pyppeteer.errors import TimeoutError as BrowserTimeoutError

from os import getenv

from typing import TypeVar, Optional, Union, Callable


_function = TypeVar('_function', bound=Callable[..., object])
_exceptions = TypeVar('_exceptions', bound=Optional[Union[str, tuple, list]])


class ExceptionDecorator:
    __default_exception = BrowserTimeoutError

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
            except Exception as caughtException:
                if type(self.__exception) == type:
                    print(caughtException)  # TODO remove later
                    if not type(caughtException) == self.__exception:
                        from aiofiles import open

                        async with open(f'.webdriver.log', 'w') as out:
                            await out.write(f'unexpected error - {caughtException}')
                else:
                    if not type(caughtException) in self.__exception:
                        from aiofiles import open

                        async with open(f'.webdriver.log', 'w') as out:
                            await out.write(f'unexpected error - {caughtException}')

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
    ) -> 'ElementHandleCls':
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
            options: Optional[dict] = None,
            el: Optional[ElementHandleCls] = None,
    ) -> None:
        if not el:
            el = await self.find_xpath(page_instance, xpath, find_options)
        if options:
            await el.click(options)
        else:
            await el.click()

    @catch_exception
    async def screenshot(
            self,
            page_instance: Optional[PageCls] = None,
            xpath: Optional[str] = None,
            options: Optional[dict] = None,
            find_options: Optional[dict] = None,
            el: Optional[ElementHandleCls] = None,
    ) -> None:
        if not el:
            el = await self.find_xpath(page_instance, xpath, find_options)
        if options:
            await el.screenshot(options)
        else:
            await el.screenshot()


class RedditScreenshot(Browser, Wait):
    __dark_mode = getenv('dark_theme', 'True') if getenv('dark_theme', 'True') else 'True'
    __dark_mode_enabled = False
    __is_nsfw_enabled = False

    async def dark_theme(
            self,
            page_instance: PageCls,
    ) -> None:
        if self.__dark_mode == 'True' and not self.__dark_mode_enabled:
            self.__dark_mode_enabled = True

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

        if is_nsfw and not self.__is_nsfw_enabled:
            self.__is_nsfw_enabled = True
            await self.click(
                reddit_main,
                '//button[contains(text(), \'Yes\')]',
                {'timeout': 5000},
            )

            await self.click(
                reddit_main,
                '//button[contains(text(), \'nsfw\')]',
                {'timeout': 5000},
            )

        await self.screenshot(
            reddit_main,
            f'//*[contains(@id, \'{el_class}\')]',
            {'path': f'assets/img/{filename}.png'},
        )
