from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from os import getenv


async def get_screenshot(
        link: str,
        class_id: str,
        filename: str
):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(link)
    if bool(getenv('dark_theme', False)):
        driver.find_element(by=By.XPATH, value='//*[contains(@class, \'header-user-dropdown\')]').click()
        driver.find_element(by=By.XPATH, value='//*[contains(text(), \'Settings\')]').click()
        driver.find_element(by=By.XPATH, value='//*[contains(text(), \'Dark Mode\')]').click()

    driver.find_element(by=By.XPATH, value=f'//*[contains(@id, \'t1_{class_id}\')]').screenshot(filename)
