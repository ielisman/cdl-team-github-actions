from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import sys
import os

url = ""
if (len(sys.argv) > 2):
  url = sys.argv[2]
else:
  print("URL is not supplied. Quiting")
  quit()

# Configure Chrome options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

# Initialize the Chrome webdriver with WebDriver Manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Navigate to the website URL
driver.get(url)

# Retrieve the website title
title = driver.title
os.environ['TITLE'] = title
os.environ['TEST123'] = 'TESTOK123'

# Print the website title to the console
print(f"title={title}; URL={os.environ['URL']}; LOGIN={os.environ['LOGIN']}; LOGIN_PAGE_ID_EMAIL={os.environ['LOGIN_PAGE_ID_EMAIL']}; ")

# Close the webdriver
driver.quit()
