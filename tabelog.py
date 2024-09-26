from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

def setup_driver(headless=False):
    """設置 Chrome 瀏覽器"""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')  # 無頭模式
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_restaurants(driver, base_url, num_pages):
    """抓取餐廳數據"""
    all_restaurants = []
    
    for page in range(1, num_pages + 1):
        url = base_url.format(page)
        driver.get(url)
        time.sleep(5)  

        # 檢查頁面是否存在餐廳
        restaurant_elements = driver.find_elements(By.CLASS_NAME, 'list-rst')
        if not restaurant_elements:
            print(f"頁面 {page} 中沒有餐廳。")
            break  # 如果沒有餐廳，則停止抓取

        # 提取餐廳信息
        for restaurant in restaurant_elements:
            try:
                name = restaurant.find_element(By.TAG_NAME, 'a').text
                link = restaurant.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                # 等待元素出現來獲取評分  <span class="c-rating__val c-rating__val--strong list-rst__rating-val">3.60</span>
                rating = WebDriverWait(restaurant, 10).until(
                    EC.visibility_of_element_located((By.XPATH, ".//span[contains(@class, 'c-rating__val')]"))
                ).text
                
                # 等待等待元素出現來獲取地點  <div class="list-rst__area-genre cpy-area-genre"> 銀座一丁目車站 / 燒肉, 烤內臟, 創新 </div>
                location = WebDriverWait(restaurant, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'list-rst__area-genre'))
                ).text.split(" / ")[0]  # 提取第一部分

                # 添加到列表
                all_restaurants.append({
                    "餐廳名稱": name,
                    "評分": rating,
                    "地點": location,
                    "網址": link
                })

            except Exception as e:
                print(f"抓取數據失敗: {e}")

    return all_restaurants

def save_to_csv(data, filename):
    """將數據保存為 CSV 文件"""
    df = pd.DataFrame(data)
    df['評分'] = pd.to_numeric(df['評分'], errors='coerce')  # 將評分轉為數字類型
    df = df.sort_values(by='評分', ascending=False)
    df.to_csv(filename, index=False, encoding='utf-8-sig')

def main():
    base_url = "https://tabelog.com/tw/tokyo/rstLst/{}/"
    num_pages = 10
    driver = setup_driver(headless=True)  # 設定為 False 可關閉無頭模式

    try:
        all_restaurants = scrape_restaurants(driver, base_url, num_pages)
        save_to_csv(all_restaurants, 'restaurants.csv')
        print(f"共計頁數: {len(all_restaurants)//10}")  
        print("資料已儲存為 restaurants.csv")
    finally:
        driver.quit()  # 關閉瀏覽器

if __name__ == "__main__":
    main()
