# import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

# Fill your login info here
email = ""
password = ""

chrome_options = webdriver.ChromeOptions()
chrome_options.headless = True
driver = webdriver.Chrome("chromedriver.exe", options=chrome_options)
wait = WebDriverWait(driver, 10)
print("=> Loading...")

driver.get("http://global.longmandictionaries.com/auth/login")
driver.find_element_by_id("email").send_keys(email)
driver.find_element_by_id("password").send_keys(password)
driver.find_element_by_id("submit").click()

driver.get("http://global.longmandictionaries.com/ldoce6/advanced_search")
driver.find_element_by_id("corevocab-button").click()
driver.find_element_by_link_text("All").click()
driver.find_element_by_id("search_submit").click()

with open("data.txt", "a", encoding="utf-8") as file:
    i = 1
    previous_id = "*"
    while True:
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, f"//*[@id='word_list']/div/div[1]/ul/li[{i}]")))
        except:
            break
        item = driver.find_element_by_xpath(f"//*[@id='word_list']/div/div[1]/ul/li[{i}]")
        word = item.find_element_by_tag_name("a")
        word.location_once_scrolled_into_view
        word.click()

        # Wait for the page to load
        # time.sleep(1)
        entry = driver.find_element_by_class_name("entry")
        wait.until(EC.staleness_of(entry))
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "entry")))
        wait.until(lambda d: d.find_element_by_class_name("entry").get_attribute("id") != previous_id)
        entry = driver.find_element_by_class_name("entry")
        current_id = entry.get_attribute("id")

        # Pass the page to Beautiful Soup
        html = entry.get_attribute("innerHTML")
        soup = BeautifulSoup(html, "html.parser")

        print(f"{i}. {current_id}")
        previous_id = current_id
        i += 1

print("=> Extract complete!")
print("=> Exiting...")
driver.quit()
