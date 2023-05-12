from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import sys

# Get the website URL from command line argument
url = sys.argv[1]

# Configure Chrome options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

# Initialize the Chrome webdriver with WebDriver Manager
driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)

# Navigate to the website URL
driver.get(url)

# Retrieve the website title
title = driver.title

# Print the website title to the console
print(title)

# Close the webdriver
driver.quit()