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
    _chrome_options.add_argument("--headless")
    _chrome_options.add_argument("–-disable-notifications")
    _chrome_options.add_argument("--window-size=%s" % _window_size)
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=_chrome_options)


class Screenshot:
    _method: str = By.XPATH
    _timeout: int = 5
    __driver = Driver().driver
    __dark_mode_enabled: bool = False

    def find_element(
            self,
            el: str,
    ):
        try:
            return WebDriverWait(self.__driver, self._timeout).until(ec.presence_of_element_located((self._method, el)))
        except TimeoutException:
            raise ValueError('Cant find_element comment on the page')

    def __call__(self,
                 link: str,
                 el_class: str,
                 filename: str,
                 is_nsfw: bool = False,
                 ) -> None:
        self.__driver.get(link)

        if bool(getenv('dark_theme', False)) and self.__dark_mode_enabled:
            self.__dark_mode_enabled = True
            self.find_element('//*[contains(@class, \'header-user-dropdown\')]').click()
            try:
                self.find_element('//*[contains(text(), \'Settings\')]').click()
            except TimeoutException:
                pass  # Sometimes there's no Settings (lol idk)
            self.find_element('//*[contains(text(), \'Dark Mode\')]').click()

        if is_nsfw:
            try:  # Closes nsfw warning if there is one
                self.find_element('//*[contains(text(), \'Yes\')]').click()
            except TimeoutException:
                pass

        self.find_element(f'//*[contains(@id, \'t1_{el_class}\')]').screenshot(filename)
