import road_test_constants as const
import os

from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

def is_element_present(by, value):
    try: driver.find_element(by=by, value=value)
    except NoSuchElementException as e: return False
    return True

chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    driver.get(const.ROAD_TEST_URL)
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_USERNAME).clear()
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_USERNAME).send_keys(os.environ['NYAKTS_USERNAME'])
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_PASSWORD).clear()
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_PASSWORD).send_keys(os.environ['NYAKTS_PASSWORD'])  
    driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_LOGIN).click()
    if is_element_present(by=By.ID, value=const.LOGIN_PAGE_ID_CONFIRM):
        driver.find_element(by=By.ID, value=const.LOGIN_PAGE_ID_CONFIRM).click()
    

except Exception as e:
    print('Not Registered',f"Exception occurred: {e}")