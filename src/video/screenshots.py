from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from os import getenv


class Driver:
    _window_size = "1920,1080"
    _chrome_options = Options()
    _chrome_options.add_argument("--headless")  # Open in background
    _chrome_options.add_argument("start-maximized")
    _chrome_options.add_argument("--window-size=%s" % _window_size)
    _chrome_options.add_argument("–-disable-notifications")
    _chrome_options.add_argument("--disable-extensions")
    _chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2
    })  # 2 - blocks all notifications, 1 - allows

    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=_chrome_options)


class Wait:
    _method: str = By.XPATH
    _timeout: int = 5
    _driver = Driver().driver

    def find_element(self, el: str,) -> 'webdriver':
        return WebDriverWait(self._driver, self._timeout).until(ec.presence_of_element_located((self._method, el)))

    def find_element_clickable(self, el: str,) -> 'webdriver':
        return WebDriverWait(self._driver, self._timeout).until(ec.element_to_be_clickable((self._method, el)))


class RedditScreenshot(Wait):
    __dark_mode_enabled: bool = False

    def __call__(self,
                 link: str,
                 el_class: str,
                 filename: str,
                 is_nsfw: bool = False,
                 ) -> None:
        if bool(getenv('dark_theme', True)) and not self.__dark_mode_enabled:
            self.__dark_mode_enabled = True
            self._driver.get('https://reddit.com/')
            self.find_element('//*[contains(@class, \'header-user-dropdown\')]').click()
            try:
                self.find_element_clickable('//*[contains(text(), \'Settings\')]').click()
            except TimeoutException:
                pass  # Sometimes there's no Settings (lol idk)
            self.find_element('//*[contains(text(), \'Dark Mode\')]').click()

        self._driver.get(link)

        if is_nsfw:
            try:  # Closes nsfw warning if there is one
                self.find_element('//*[contains(text(), \'Yes\')]').click()
            except TimeoutException:
                pass

        self.find_element(f'//*[contains(@id, \'t1_{el_class}\')]').screenshot(filename)
