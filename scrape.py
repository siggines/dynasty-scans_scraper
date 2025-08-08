from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException
import time
import os
import requests

service = Service('./geckodriver')
driver = webdriver.Firefox(service=service)
wait = WebDriverWait(driver, 10)

MAIN_URL = "https://dynasty-scans.com/tags/incest"

def safe_filename(name):
    return "".join(c for c in name if c.isalnum() or c in " _-").rstrip()

def click_next_page(current_page_num):
    next_page_num = current_page_num + 1
    try:
        next_page_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'a.page[href="#{next_page_num}"]')))
        print(f"Clicking page {next_page_num}")
        next_page_link.click()
        time.sleep(2)
        return next_page_num
    except TimeoutException:
        print("No more pages found.")
        return None

def click_download_and_save(page_num, folder):
    try:
        download = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a#download_page.btn.btn-mini')))
        img_url = download.get_attribute('href')
        print(f"Downloading page {page_num} from {img_url}")

        response = requests.get(img_url)
        if response.status_code == 200:
            os.makedirs(folder, exist_ok=True)
            filename = os.path.join(folder, f"page_{page_num}.webp")
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Saved image as {filename}")
        else:
            print(f"Failed to download image from {img_url}")

        time.sleep(2)
    except TimeoutException:
        print("No page download button found on this page.")

try:
    page_num = 1

    while True:
        driver.get(f"{MAIN_URL}?page={page_num}&view=chapters")
        time.sleep(3)

        try:
            book_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.name[href^="/chapters/"]')))
        except TimeoutException:
            print(f"No books found on page {page_num}, stopping.")
            break

        if not book_links:
            print(f"No books found on page {page_num}, stopping.")
            break

        print(f"Page {page_num}: Found {len(book_links)} books")

        for i in range(len(book_links)):
            book_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.name[href^="/chapters/"]')))
            book = book_links[i]
            book_href = book.get_attribute('href')

            parent = book.find_element(By.XPATH, '..')
            try:
                series_link = parent.find_element(By.CSS_SELECTOR, 'a[href^="/series/"]')
                book_name = series_link.text.strip()
            except:
                book_name = book_href.split('/')[-1]

            folder_name = safe_filename(book_name)
            print(f"Processing book {i+1}/{len(book_links)} on page {page_num}: {book_name} ({book_href})")
            book.click()
            time.sleep(3)

            click_download_and_save(1, folder_name)

            current_page = 1
            while True:
                next_page = click_next_page(current_page)
                if not next_page:
                    break
                current_page = next_page
                click_download_and_save(current_page, folder_name)

            print("Pages exhausted. Returning to book list.")
            driver.get(f"{MAIN_URL}?page={page_num}&view=chapters")
            time.sleep(3)

        page_num += 1

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()
