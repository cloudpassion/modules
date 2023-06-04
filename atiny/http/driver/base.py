import random
import os
import asyncio
import threading
import pickle

try:
    from log import logger, log_stack
except ImportError:
    from ...log import logger, log_stack

# TODO: fix
try:
    from fake_useragent import UserAgent
    from collections import deque
    from datetime import datetime
    from selenium import webdriver
    from seleniumwire import webdriver as selenium_webdriver
    import seleniumwire.undetected_chromedriver as uc

    from selenium.webdriver.support.ui import WebDriverWait

    # from selenium_stealth import stealth

    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.proxy import (
        Proxy as SeleniumProxy, ProxyType as SeleniumProxyType
    )
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium import webdriver as wb
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
    from selenium.webdriver.common.keys import Keys
except ImportError:
    logger.info(f'selenium')

from config import settings

from ...http.proxy import Proxy
from .stuff import DriversStuff
from .wire import WireRequestsWatcher


class Drivers(
    DriversStuff, WireRequestsWatcher
):

    def __init__(
            self, limit=2, proxies=None, data_file='', driver_url=None, watch=False,
            use_wire=False, get_limit=4,
    ):
        self.limit = limit
        self.completed = {}
        self.requests = deque()
        self.sniff_urls = set()
        self.block_urls = set(settings.chrome.blocked_urls)

        self.watch = watch
        self.use_wire = use_wire
        self.get_sem = asyncio.Semaphore(get_limit)

        if driver_url:
            self.driver_url = driver_url
        else:
            self.driver_url = settings.chrome.driver_url

        if proxies is False:
            self.proxies = [
                *[Proxy(
                    f'http://192.168.55.125:{x}',
                ) for x in range(
                    # 11100, int(f'111{self.complete_sem_max}')
                    11100, int(f'11141')
                )],
            ]
        else:
            self.proxies = proxies

        self.data_file = data_file
        self.data = self.load_data()

    def save_data(self):
        data_file = self.data_file
        data = {}
        for key, value in self.data.items():
            data[key] = {
                k: v for k, v in value.items() if k != 'driver'
            }

        with open(data_file, 'wb') as dw:
            dw.write(pickle.dumps(data))

    def load_data(self):

        data_file = self.data_file
        if not data_file:
            return {}

        if not os.path.isfile(data_file):
            return {}

        if os.stat(data_file).st_size == 0:
            return {}

        try:
            with open(data_file, 'rb') as dr:
                data = pickle.loads(dr.read())
        except:
            return {}

        if not data:
            return {}

        return data

    def get_wire_options(self, proxy=None):

        wire_options = {}
        if proxy:
            wire_options.update({
                'proxy': {
                    'http': f'{proxy.aio_str}',
                    # 'https': f'{proxy.aio_str}',
                    'no_proxy': f'localhost,127.0.0.1,{proxy.adr}'
                }
            })

        wire_options.update({
            'auto_config': True,
            'addr': '192.168.65.125',
        })
        wire_options.update({
            'disable_capture': False,
            'request_storage': 'memory',
            'suppress_connection_errors': False,
            'verify_ssl': True
        })

        return wire_options

    def get_options(
            self, proxy=None
    ):

        # options = webdriver.ChromeOptions()
        options = uc.ChromeOptions()
        if proxy:
            options.add_argument(f'--proxy-server={proxy.aio_str}')

        # options.add_argument('--disable-infobars')
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'user-agent={user_agent}')

        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')

        # options.add_argument("--incognito")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-gpu")
        options.add_argument('--disable-notifications')
        options.add_argument("--mute-audio")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # options.add_argument("start-maximized")

        return options

    # check execute url if already running
    def check_driver(self, session_id, check_net=True):

        global webdriver
        session_data = self.data.get(session_id)

        if not session_data:
            return

        executor = session_data.get('executor')
        if not executor:
            return

        driver = session_data.get('driver')
        if not driver:
            proxy = session_data.get('proxy')

            org_command_execute = webdriver.Remote.execute

            def new_command_execute(self, command, params=None):
                if command == "newSession":
                    # Mock the response
                    return {'success': 0, 'value': None, 'sessionId': session_id}
                else:
                    return org_command_execute(self, command, params)

            kwargs = {}
            if self.use_wire:
                options = self.get_options(
                    # proxy=proxy,
                )
                wire_options = self.get_wire_options(
                    proxy=proxy
                )
                kwargs.update({
                    'seleniumwire_options': wire_options,
                })
                webdriver = selenium_webdriver
            else:
                options = self.get_options(
                    proxy=proxy,
                )

            webdriver.Remote.execute = new_command_execute

            driver = webdriver.Remote(
                command_executor=executor,
                desired_capabilities=options.to_capabilities(),
                **kwargs
            )

            driver.session_id = session_id

            # if settings.chrome.blocked_urls:
            #     self.send(driver, 'Network.setBlockedURLs', {
            #         "urls": list(settings.chrome.blocked_urls)
            #     })
            #     self.send(driver, 'Network.enable', {})

            webdriver.Remote.execute = org_command_execute

        try:
            source = driver.page_source
        except:
            try:
                self.remove_driver(session_id)
            except:
                pass

            return

        self.data[session_id]['driver'] = driver
        if self.watch:
            self.run_watcher_thread(driver)
        return driver

    # first time create
    def create_driver(self, proxy):

        global webdriver

        kwargs = {}
        if self.use_wire:
            options = self.get_options(
                # proxy=proxy,
            )
            wire_options = self.get_wire_options(
                proxy=proxy
            )
            kwargs.update({
                'seleniumwire_options': wire_options,
            })
            webdriver = selenium_webdriver
        else:
            options = self.get_options(
                proxy=proxy,
            )

        driver = webdriver.Remote(
            command_executor=self.driver_url,
            desired_capabilities=options.to_capabilities(),
            **kwargs
        )

        # if settings.chrome.blocked_urls:
        #     self.send(driver, 'Network.setBlockedURLs', {
        #         "urls": list(settings.chrome.blocked_urls)
        #     })
        #     self.send(driver, 'Network.enable', {})

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        # self.send(driver, 'Network.setUserAgentOverride', {"userAgent": user_agent.random})

        # stealth(driver,
        #         languages=["en-US", "en"],
        #         vendor="Google Inc.",
        #         platform="Win32",
        #         webgl_vendor="Intel Inc.",
        #         renderer="Intel Iris OpenGL Engine",
        #         fix_hairline=True,
        #         )

        if self.watch:
            self.run_watcher_thread(driver)
        return driver

    def get_driver(self, proxy=None):

        driver = None

        if proxy:
            for sid, data in self.data.items():
                if data.get(proxy) == proxy:
                    driver = data.get('driver')
                    break

        else:
            driver = random.choice([x.get('driver') for x in self.data.values()])

        if not driver:
            self.init_drivers()
            driver = self.get_driver()

        return driver

    def remove_driver(self, session_id):

        session_data = self.data.get(session_id)
        if session_data:
            driver = session_data.get('driver')
            del self.data[session_id]
            if driver:
                try:
                    driver.close()
                except:
                    pass
                try:
                    driver.quit()
                except:
                    pass

    def init_drivers(self):

        proxies = self.proxies.copy()

        for session_id, session_data in self.data.copy().items():
            check = self.check_driver(session_id)
            if not check:
                self.remove_driver(session_id)
        
        for x in range(len(self.data.keys()), self.limit):

            current_proxies = [
                x['proxy'].aio_str for x in self.data.values() if x.get('proxy')
            ]
            try:
                proxy = proxies.pop()
            except IndexError:
                proxy = None

            if proxy:
                c = 1
                while proxy.aio_str in current_proxies:
                    c += 1
                    try:
                        proxy = proxies.pop()
                    except:
                        proxies = self.proxies.copy()
                        continue

                    if c > len(self.proxies):
                        rnd = random.randint(0, len(self.proxies)-1)
                        proxy = proxies[rnd]

            driver = self.create_driver(proxy)
            self.data[driver.session_id] = {
                'proxy': proxy, 'driver': driver,
                'executor': driver.command_executor._url,
                'time': datetime.now()
            }

        self.save_data()

    def _run_thread(self, load_hash, func, *args, **kwargs):
        try:
            ret = func(*args)
        except Exception as exc:
            ret = exc

        self.completed[load_hash] = ret if ret else True

    def run_thread(self, *args, **kwargs):
        load_hash = random.getrandbits(128)
        get_thread = threading.Thread(
            target=self._run_thread, args=(load_hash, *args), kwargs=kwargs
        )
        get_thread.start()
        return load_hash

    async def wait_thread(self, load_hash):

        while True:
            check = self.completed.get(load_hash)

            if check:
                break

            await asyncio.sleep(0.1)

        return check

    async def refresh_page(self, driver, wait=True):
        load_hash = self.run_thread(driver.refresh)
        if wait:
            await self.wait_thread(load_hash)
            return driver, driver.page_source
        
        return driver, load_hash

    async def get_page(self, url, driver, wait=True):

        load_hash = self.run_thread(driver.get, url)
        if wait:
            await self.wait_thread(load_hash)

            html = driver.page_source

            return driver, html

        return driver, load_hash
