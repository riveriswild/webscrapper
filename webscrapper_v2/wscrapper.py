import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import unicodedata

cities = ['Санкт-Петербург и Ленинградская область', 'Москва и Московская область']

def write_csv(products, document):
    """ Generate csv file

    Args:
        products (dict): dictionary of products
        document (str): name for output csv file
    """        
    with open(document, 'a') as f:
        fields = ['id','title','price', 'promo_price', 'url']
        writer = csv.DictWriter(f, delimiter=',', fieldnames=fields)
        writer.writeheader()
        
        
        for product in products:
            writer.writerow(product)
            

''' PRIMARY SELENIUM SETTING '''
options = Options()
options.headless = True
options.add_argument("window-size=1200x600")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


''' PRIMARY REQUEST '''
driver.get('https://www.detmir.ru/catalog/index/name/lego/page/1/')

def choose_city(city):
    """ Open the popup, choose city and click on it

    Args:
        city (str): city name
    """    
    el = driver.find_element(By.XPATH,
            
                            '//*[@id="app-container"]/div[2]/header/div[2]/div/div[1]/ul/li[1]/div/div/div[1]/div/span')
    el.click()
    print('Выбираю город...')
    driver.implicitly_wait(10)
    cities_list_el = driver.find_elements(By.CSS_SELECTOR, 'body > div > div > div > section > div > ul > li > ul > li')
    for option in cities_list_el:
        if option.text == city:
            option.click()
            break
        else:
            print('error')
    driver.implicitly_wait(10)
    print("Выбран город:", el.text)
    return

def get_page_count():
    """
    Go through pages as long as product elements are present and count total number of pages

    Returns:
        int: number of pages in category
    """    
    counter = 0  
    print("Оцениваю количество страниц. Я не завис, я просто медленный")
    while driver.find_elements(By.CSS_SELECTOR,
                           '#app-container > div.p > main > div > div > div > div > div > div > div > div > div > div > div > a'):
        counter += 1
        driver.get(f'https://www.detmir.ru/catalog/index/name/lego/page/{counter}/')
    return counter

def get_html(url):
    """ get HTML source of the page

    Args:
        url (str): URL to get

    Returns:
        str: the HTML source of the page
    """    
    driver.get(url)
    return driver.page_source

def scrape_data(card):
    """ Parse data into dictionary

    Args:
        card (str): data of a single product

    Returns:
        dict: parsed data of a single product
    """   
    data = {}
    title = card.p.text
    url = card.get('href')
    id = url.strip('/').split('/')[-1]
    # id = re.findall('\d+', link)   # possible but gives a ['id'] 
    prices_raw = card.select_one('a > div > div > div:nth-child(2) > div > div').text 
    prices = unicodedata.normalize("NFKD", prices_raw).strip('').split(' ₽')  # ['249', ''] why??
    if len(prices) == 3:
        price = prices[1]
        promo_price = prices[0]
    else: 
        price = prices[0]
        promo_price = None
    
    data = {'id': id, 'title': title, 'price': price, 'promo_price': promo_price, 'url': url}
        
    return data   
    
def main(): 
    for city in cities:
        product_data = []
        choose_city(city)
        count = get_page_count()   # можно вытащить из цикла, чтобы не гонять лишний раз ф-цию, если не собираем исключительно продукты в наличии: у всех городов одно кол-во страниц   
        for i in range(1, count):
            print(f'Обрабатываю данные со страницы {i} из {count-1} ')    
            url = f'https://www.detmir.ru/catalog/index/name/lego/page/{i}/'
            html = get_html(url)
            soup = BeautifulSoup(html, 'lxml')
            cards = soup.select('#app-container > div.p > main > div > div > div > div > div > div > div > div > div > div > div > a')
            # cards = soup.find_all('a', href=re.compile('product/index/id/')) # TODO products from promos!!! not lego
            cards_clean = [card for card in cards if 'LEGO' in card.text] # TODO still bad for performance but a bit better; fix if possible
            for card in cards_clean:   
                    data = scrape_data(card)
                    product_data.append(data)
        document = city + '_' + 'products.csv'
        print(f'Записываю данные по городу {city} в документ {document}')
        write_csv(product_data, document)
    print('Готово!')
        
    

if __name__ == '__main__':
    main()