import json
import re
import time
import pytest

from urllib.parse import urljoin

from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

BASE_URL = "https://demo.vamshop.com/"
PRODUCT_LIST = ["product/samsung-gear-2-charcoal-black.html",
                "product/samsung-ativ-book-4.html",
                "product/samsung-galaxy-s4.html"]

# The scope is "module" so we do not have to request the token every time
@pytest.fixture(scope="module")
def data():
    with open("resources/data.json") as json_file:
        json_data = json.load(json_file)
    return json_data

@pytest.fixture
def cart_mapping():
    with open("resources/cart_mapping.json") as json_file:
        json_data = json.load(json_file)
    return json_data

@pytest.fixture
def coupon_mapping():
    with open("resources/coupon_mapping.json") as json_file:
        json_data = json.load(json_file)
    return json_data

@pytest.fixture
def driver():
    _driver = Chrome()
    yield _driver
    _driver.quit()

def add_product_to_cart(driver, url):
    driver.get(urljoin(BASE_URL, url))
    element = driver.find_element(By.XPATH, '//button[@type="submit" and text()=" Add to cart"]')
    element.click()
    return driver.find_element(By.XPATH, '//h2[@itemprop="name"]').text

def add_list_products_to_cart(driver, url_list):
    products = []
    for url in url_list:
        products.append(add_product_to_cart(driver, url))
    return products

def admin_login(driver, username, password):
    driver.get(urljoin(BASE_URL, "users/admin_login/"))
    input_user = driver.find_element(By.XPATH, '//input[@id="UserUsername"]')
    input_user.send_keys(username)
    input_password = driver.find_element(By.XPATH, '//input[@id="UserPassword"]')
    input_password.send_keys(password)
    submit_button = driver.find_element(By.XPATH, '//button[text()=" Login"]')
    submit_button.click()

def correct_admin_login(driver, data):
    admin_login(driver, data['user'], data['password'])

def new_user_login(driver, data):
    admin_login(driver, data['new_user'], data['new_password'])

def wrong_admin_login(driver, data):
    admin_login(driver, data['user'], data['wrong_password'])

def logout_admin_account(driver):
    driver.get(urljoin(BASE_URL, "/users/admin_logout/"))

def test_mentormate_1(driver):
    # Load the base url:
    driver.get(BASE_URL)

    # Find the smartwatches section and click
    element = driver.find_element(By.XPATH, '//h4[@class="title" and text()=" Smart Watches"]')
    element.click()
    assert "https://demo.vamshop.com/category/smart-watches.html" == driver.current_url, "The button does not load the correct URL"

def test_mentormate_2(driver):
    # Load smartwatches URL:
    driver.get(urljoin(BASE_URL, "category/smart-watches.html"))

    # Find the first product on the page:
    element = driver.find_element(By.XPATH, '//li[@class="item col-sm-3 col-md-4"]')
    element.click()
    html = driver.page_source
    assert '<span class="price">' in html, "Price is missing from product details"
    assert '<div class="product-images">' in html, "Product images are missing from product details"
    assert '<b> Select Color:' in html, "Selection of color is missing from product details"
    assert '<button type="submit"' in html, "'Add to cart' button is missing from product details"

def test_mentormate_4(driver):
    # Load smartwatches URL:
    driver.get(urljoin(BASE_URL, "product/samsung-gear-2-charcoal-black.html"))

    # Find the Add to cart button and click
    element = driver.find_element(By.XPATH, '//button[@type="submit" and text()=" Add to cart"]')
    element.click()
    driver.get(urljoin(BASE_URL, "page/cart-contents.html"))
    assert "Samsung Gear 2 Charcoal Black" in driver.page_source, "Expected product is not added to the cart"

def test_mentormate_5(driver):
    products = add_list_products_to_cart(driver, PRODUCT_LIST)

    driver.get(urljoin(BASE_URL, "page/cart-contents.html"))
    html = driver.page_source

    for product in products:
        assert product in html, f"{product} not added to the cart"
    
    element = driver.find_element(By.XPATH, f'//td/a[text()="{products[0]}"]/following::a[@class="remove"]')
    element.click()
    assert products[0] not in driver.page_source, "Product is not removed from the cart"

def test_mentormate_6(driver):
    n = 3
    temp_product_list = ["product/samsung-gear-2-charcoal-black.html"] * n
    product = add_list_products_to_cart(driver, temp_product_list)[0]

    driver.get(urljoin(BASE_URL, "page/cart-contents.html"))
    html = driver.page_source
    assert product in html, f"{product} not added to the cart"
    price_before = driver.find_element(By.XPATH, f'//tbody/tr[not(@class)]/td[last()]').text
    price_before = int(re.findall(r'\d+', price_before)[0])
    
    element = driver.find_element(By.XPATH, f'//td/a[text()="{product}"]/following::a[@class="remove"]')
    element.click()
    price_after = driver.find_element(By.XPATH, f'//tbody/tr[not(@class)]/td[last()]').text
    price_after = int(re.findall(r'\d+', price_after)[0])

    assert product in driver.page_source, f"Product removed from the cart. Expected to have {n-1}"
    assert price_before/n == price_after/(n-1), "The product price calculation is faulty"

def test_mentormate_7(driver, data):
    correct_admin_login(driver, data)
    assert "https://demo.vamshop.com/admin/admin_top/" == driver.current_url, "Login with correct credentials was not accepted"

def test_mentormate_8(driver, data):
    wrong_admin_login(driver, data)
    assert "https://demo.vamshop.com/admin/admin_top/" != driver.current_url, "Login incorrectly accepted! Redirected to the admin page withput proper rights"
    
    message = driver.find_element(By.XPATH, f'//div[@id="flashMessage"]')
    assert "No match for Username and/or Password." == message.text, "Login incorrectly accepted! Does not show the correct message"
    
def test_mentormate_9(driver, data):
    correct_admin_login(driver, data)
    driver.get(urljoin(BASE_URL, "users/admin/"))

    create_new_button = driver.find_element(By.XPATH, f'//a[text()=" Create New"]')
    create_new_button.click()
    input_user = driver.find_element(By.XPATH, '//input[@id="UserUsername"]')
    input_user.send_keys(data['new_user'])

    input_password = driver.find_element(By.XPATH, '//input[@id="UserPassword"]')
    input_password.send_keys(data['new_password'])

    input_email = driver.find_element(By.XPATH, '//input[@id="UserEmail"]')
    input_email.send_keys(data['new_email'])

    submit_button = driver.find_element(By.XPATH, '//button[text()=" Submit"]')
    submit_button.click()

    message = driver.find_element(By.XPATH, f'//div[@id="flashMessage"]')
    assert "Record created." == message.text, "Account was not able to be recorded"
    
    logout_admin_account(driver)
    new_user_login(driver, data)
    assert "https://demo.vamshop.com/admin/admin_top/" == driver.current_url, "Login with correct credentials was not accepted"

def test_mentormate_10(driver, data, cart_mapping):
    products = add_list_products_to_cart(driver, PRODUCT_LIST)
    driver.get(urljoin(BASE_URL, "page/checkout.html"))

    for elem, value in cart_mapping.items():
        input_email = driver.find_element(By.XPATH, f'//input[@id="{elem}"]')
        input_email.send_keys(value)

        # Fill form is buggy, Should be fixed by developers. WA: sleep for 1s per entry
        time.sleep(1)

    driver.find_element(By.XPATH, '//button[text()=" Continue"]').click()
    element_present = EC.presence_of_element_located((By.XPATH, '//button[text()=" Confirm Order"]'))
    WebDriverWait(driver, 10).until(element_present)
    driver.find_element(By.XPATH, '//button[text()=" Confirm Order"]').click()
    element_present = EC.presence_of_element_located((By.XPATH, '//h2[text()="Thank You"]'))
    WebDriverWait(driver, 10).until(element_present)

    correct_admin_login(driver, data)
    driver.get(urljoin(BASE_URL, "orders/admin/"))
    
    bill_name = cart_mapping['bill_name']
    html = driver.page_source
    assert bill_name in driver.page_source, "The order is not present in the order list"

    driver.find_element(By.XPATH, f'//a[text()="{bill_name}"]').click()
    html = driver.page_source
    assert "Billing Information" in html, "No billing information present in the resulting page"
    assert "Shipping Information" in html, "No shipping information present in the resulting page"
    logout_admin_account(driver)

def test_mentormate_12(driver, data, coupon_mapping):
    correct_admin_login(driver, data)
    driver.get(urljoin(BASE_URL, "module_coupons/admin/admin_index/"))
    driver.find_element(By.XPATH, '//a[text()=" Create New"]').click()
    
    for elem, value in coupon_mapping.items():
        input_field = driver.find_element(By.XPATH, f'//input[@id="{elem}"]')
        input_field.send_keys(value)

    driver.find_element(By.XPATH, '//button[text()=" Submit"]').click()
    assert "You have updated a coupon." in driver.page_source, "The message for update of coupon did not show up."

    driver.get(urljoin(BASE_URL, "module_coupons/admin/admin_index/"))
    assert coupon_mapping["ModuleCouponName"] in driver.page_source, "Coupon is missing from the coupon list"
    logout_admin_account(driver)

def test_mentormate_14(driver, data):
    driver.get(urljoin(BASE_URL, "page/contact-us.html"))

    driver.find_element(By.XPATH, f'//input[@id="name"]').send_keys("Some One")
    driver.find_element(By.XPATH, f'//input[@id="email"]').send_keys("someone@somewhere.tt")
    driver.find_element(By.XPATH, f'//textarea[@id="message"]').send_keys("This is some comment")
    driver.find_element(By.XPATH, '//button[text()=" Send"]').click()
    assert " Your enquiry has been successfully sent!" in driver.page_source, "The message for successful contact did not show up."

    correct_admin_login(driver, data)
    driver.get(urljoin(BASE_URL, "contact_us/admin/"))
    assert "someone@somewhere.tt" in driver.page_source, "Contact us message is missing from the coupon list"
    logout_admin_account(driver)

if __name__ == "__main__":
    print(f"This is a test file, please run with:\npython -m pytest {__file__}")