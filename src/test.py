from .folder_manager import FolderManager
from .profile_manager import ProfileManager
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from app.multilogin.service import MultiloginService
import re
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
api_url = 'https://api.multilogin.com'
api_token = 'eyJhbGciOiJIUzUxMiJ9.eyJicGRzLmJ1Y2tldCI6Im1seC1icGRzLXByb2QtZXUtMSIsIm1hY2hpbmVJRCI6IiIsInByb2R1Y3RJRCI6Imx0Iiwid29ya3NwYWNlUm9sZSI6Im93bmVyIiwidmVyaWZpZWQiOnRydWUsInBsYW5OYW1lIjoiUHJvMTAgKHllYXJseSkiLCJzaGFyZElEIjoiY2JlMTM4MDAtYmJhZi00YzhmLTgwYjMtMTk3Zjg5NjM5NGYyIiwidXNlcklEIjoiNjdiNjU2ODgtZTYyYS00MGEyLWFhNjgtNDBmOTJkYjhlOWRlIiwiZW1haWwiOiJhbG1lcmFuZG8yQGdtYWlsLmNvbSIsImlzQXV0b21hdGlvbiI6ZmFsc2UsIndvcmtzcGFjZUlEIjoiMWQxZTY5OWYtODJlMS00ZTY2LTg4MzMtNzE5OTQ4OWJmOTFlIiwianRpIjoiNzk3NGY1OWYtZWZlZS00YmFkLWI4ZWItZWZiMTgxMzYwMWQ5Iiwic3ViIjoiTUxYIiwiaXNzIjoiNjdiNjU2ODgtZTYyYS00MGEyLWFhNjgtNDBmOTJkYjhlOWRlIiwiaWF0IjoxNzYxMjc1NzA5LCJleHAiOjE3NjEyNzkzMDl9.G4IdrrEmHWFl2-wbO1A5vAwKMX7BxMcWdD8I1fwdp5Ygcsz-KM5rk6oI85cBDXEsccbtLKtW1r98H1YNnxCu8A'
folder_id = '02155142-1026-426b-bf15-558ce422df36'
# profile_manager = ProfileManager(api_url, api_token)
folder_manager = FolderManager(api_url, api_token)

multilogin = MultiloginService()
# results = multilogin.run_profile()
results = multilogin.process_url(url='https://winesearcher.com/discover')
# results = multilogin._get_tokens()
print(results)



# proxy_config = {
#     "type": "socks5",
#     "host": "gate.multilogin.com",
#     "port": 1080,
#     "username": "154137_1d1e699f_82e1_4e66_8833_7199489bf91e_multilogin_com-country-US-sid-vJ3VUQ5LXrVjTaKS-filter-medium",
#     "password": "norvack3of",
#     "save_traffic": False
# }

# for i in range(2):
#     p = profile_manager.create_profile(folder_id=folder_id, name=f'test{i}', browser_type='mimic', os_type='windows')
#     print(p)

# f = profile_manager.get_profile_ids(folder_id=folder_id)
# print(f)

# g = profile_manager.get_profile_names(folder_id=folder_id)
# print(g)




# for i in f:
#     p = profile_manager.update_profile(profile_id=i, folder_id=folder_id, name=f'test{i}', browser_type='mimic', os_type='windows', proxy=proxy_config)
#     print(p)
# if len(f) >= 3:
#     for i in f:
#         profile_manager.delete_profile(profile_id=i)
#         print(f'Deleted profile {i}')
# for i in f:
#     p = profile_manager.create_profile(folder_id=folder_id, name='test3', browser_type='mimic', os_type='windows')
#     p = profile_manager.update_profile(profile_id=i, folder_id=folder_id, name='test3', browser_type='mimic', os_type='windows', proxy=proxy_config)
#     print(p)

# p2 = profile_manager.create_profile(folder_id=folder_id, name='test1')
# p2 = profile_manager.update_profile(profile_id='af0d21df-3be6-4958-bbf6-154f759b17d0', folder_id=folder_id, name='test3', browser_type='mimic', os_type='windows')

# print(p2)

# headers = {
#     'Accept': 'application/json',
#     "Authorization": f"Bearer {api_token}",
# }

# r = requests.get(url=f"https://launcher.mlx.yt:45001/api/v1/profile/f/{folder_id}/p/e532f5be-f441-4e8a-a22f-b611d275b89d/start?automation_type=selenium", headers=headers)

# response = r.json()

# response = response.get('status', {}).get('message')
# p_manager = MultiloginService(api_token=api_token, folder_id=folder_id, profile_id='e532f5be-f441-4e8a-a22f-b611d275b89d')
# results = p_manager.process_url(url='https://www.wine-searcher.com/discover')
# print(results)

# list_response = folder_manager.list_folders()
# folders = [folder.get('folder_id') for folder in list_response.get('data', {}).get('folders', [])]
# print(folders)
# port = p_manager.run_profile()


# selenium_port = port.get('status', {}).get('message')
# selenium_url = f"http://localhost:{selenium_port}"

# options = Options()

# options.add_argument("--disable-blink-features=AutomationControlled")  # optional, avoids detection

# driver = webdriver.Remote(
#     command_executor=selenium_url,
#     options=options
# )

# wait = WebDriverWait(driver, 10)

# driver.get("https://www.wine-searcher.com/discover")

# print(driver.title)

# def clean_dict_text(data_dict):
#     cleaned = {}
#     for key, value in data_dict.items():
#         # 1. Replace newlines and tabs with a single space
#         text = re.sub(r'[\n\t\r]+', ' ', value)
#         # 2. Remove non-printable or strange symbols (except ₱, commas, dots, colons, and parentheses)
#         text = re.sub(r"[^A-Za-z0-9₱.,:()'’/ -]+", '', text)
#         # 3. Normalize multiple spaces
#         text = re.sub(r'\s+', ' ', text).strip()
#         cleaned[key] = text
#     return cleaned

# while True:
#     try:

#         show_more = wait.until(EC.presence_of_element_located((By.ID, "pjax-discover-list-offers-only")))
#         show_more = show_more.find_element(By.TAG_NAME, "button")

#         if show_more.text == "Show more":
#             show_more.click()

#         if "Show more" in show_more.text:
#             print("Clicking Show more...")
#             show_more.click()
#             # Optional: short delay to let page load
#             time.sleep(2)
#         else:
#             print("Button found but text not matching, stopping.")
#             break
#     except (NoSuchElementException, TimeoutException):
#         print("Button not found, stopping.")
#         break
#     except StaleElementReferenceException:
#         print("Stale element reference, stopping.")
#         continue

# element = wait.until(EC.presence_of_element_located((By.ID, "selection-list-widget")))

# cards = element.find_elements(By.CSS_SELECTOR, ".flip-card.discover")
# shop_info_list = element.find_elements(By.CSS_SELECTOR, ".flip-card.py-2A")
# ratings_list = element.find_elements(By.CSS_SELECTOR, "div.position-relative > div.overlay.top.left > div > span")

# for card, shop_info, rating in zip(cards, shop_info_list, ratings_list):
#     product_info = card.find_element(By.CSS_SELECTOR, ".product-info")
#     offer_info = card.find_element(By.CSS_SELECTOR, ".offer-info")

#     data = {
#         "product_info": product_info.text,
#         "offer_info": offer_info.text,
#         "shop_info": shop_info.text,
#         "rating": rating.text
#     }

#     cleaned_data = clean_dict_text(data)

#     print(cleaned_data)
    
# driver.quit()