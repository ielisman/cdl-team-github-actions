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
  
print (f"URL={os.environ['URL']}")
print (f"LOGIN={os.environ['LOGIN']}")
print (f"PWD={os.environ['PWD']}")

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

# Print the website title to the console
print(title)

# Close the webdriver
driver.quit()
