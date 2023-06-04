try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger, log_stack
except ImportError:
    from ...log import logger, log_stack

try:
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
except ImportError:
    logger.info(f'selenium')


class DriversStuff:

    # https://stackoverflow.com/questions/46891301/can-i-automate-chrome-request-blocking-using-selenium-webdriver-for-ruby
    @staticmethod
    def send(driver, cmd, params={}):
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)

        return response.get('value')

    # def send_cmd(driver, cmd, params={})
    #     bridge = driver.send(:bridge)
    #     resource = "session/#{bridge.session_id}/chromium/send_command_and_get_result"
    #     response = bridge.http.call(:post, resource, {'cmd':cmd, 'params': params})
    #     raise response[:value] if response[:status]
    #     return response[:value]

    # send_cmd(driver, "Network.setBlockedURLs", {'urls': ["*"]})
    # send_cmd(driver, "Network.enable")
    def get_clear_browsing_button(self, driver):
        """Find the "CLEAR BROWSING BUTTON" on the Chrome settings page."""
        # return driver.find_element(By.XPATH, '//*[@id="clearBrowsingDataConfirm"]')
        return driver.find_element(By.ID, 'clearBrowsingDataConfirm')

    def clear_cache(self, driver, timeout=60):
        """Clear the cookies and cache for the ChromeDriver instance."""
        # navigate to the settings page
        driver.get('chrome://settings/clearBrowserData')

        # wait for the button to appear
        # wait = WebDriverWait(driver, timeout)
        # wait.until(self.get_clear_browsing_button)
        driver.find_element(By.XPATH, "//settings-ui").send_keys(Keys.ENTER)
        # click the button to clear the cache
        # self.get_clear_browsing_button(driver).click()

        # wait for the button to be gone before returning
        # wait.until_not(self.get_clear_browsing_button)
