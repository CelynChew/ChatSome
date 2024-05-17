import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

localhost = "http://127.0.0.1:5000"

class TestSelenium(unittest.TestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.base_url = localhost

    def tearDown(self):
        self.driver.quit()

    # Test landing page is login
    def test_home_page(self):
        self.driver.get(self.base_url)
        self.assertIn("Login", self.driver.title)  # Check title of HTML
        heading = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertEqual(heading.text, "Welcome to ChatSome!")

    # Test for redirection from base page to registration page.
    # Test for valid registration and login
    # Test for creating chats
    def test_login_and_chat_functionality(self):
        driver = self.driver

        # Test for redirection from login to register page
        driver.get(self.base_url)
        register_link = driver.find_element(By.CSS_SELECTOR, "a[href='../register']")
        register_link.click()
        WebDriverWait(driver, 10).until(EC.title_contains("Registration"))
        self.assertIn("Registration", driver.title)

        # Test for valid registration
        driver.find_element(By.ID, "uName").send_keys("test_user")
        driver.find_element(By.ID, "password").send_keys("password")
        driver.find_element(By.ID, "retypePassword").send_keys("password")
        driver.find_element(By.ID, "submit-btn").click()
        
        # Check that the page is redirected to login page
        WebDriverWait(driver, 10).until(EC.title_contains("Login"))
        self.assertIn("Login", driver.title)

        # Test for valid login after registration
        driver.find_element(By.ID, "username").send_keys("test_user")
        driver.find_element(By.ID, "password").send_keys("password")
        driver.find_element(By.ID, "login-btn").click()

        # Wait for successful entry into the chat room
        WebDriverWait(driver, 10).until(EC.title_contains("Chatroom"))
        self.assertIn("Chatroom", driver.title)

        # Test new chat button
        new_chat_btn = driver.find_element(By.ID, "new-chat-btn")
        new_chat_btn.click()

        # Wait for the new chat modal to appear
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "new-chat-form")))

        # Enter username to start a new chat
        driver.find_element(By.ID, "members-input").send_keys("test_user")
        driver.find_element(By.CSS_SELECTOR, "#new-chat-form .btn-primary").click()

        # Wait for the new chat to be added to the chat list
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//li[contains(text(), 'test_user')]")))

         # Check that new chat has been added to the chat list
        new_chat = driver.find_element(By.XPATH, "//li[contains(text(), 'test_user')]")
        self.assertIsNotNone(new_chat)

    # Test for redirection to tutorial page (from landing)
    def test_landing_to_tutorial(self):
        driver = self.driver
        
        # Test for redirection from login to register page
        driver.get(self.base_url)
        register_link = driver.find_element(By.CSS_SELECTOR, "a[href='/tutorial']")
        register_link.click()
        WebDriverWait(driver, 10).until(EC.title_contains("Tutorial"))
        self.assertIn("Tutorial", driver.title)

if __name__ == '__main__':
    unittest.main()