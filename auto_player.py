import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from easydict import EasyDict
import json

import os, sys, time

SETTINGS_FN = "settings.txt"
VIDEO_MAX = 10

class JsonConfigFileManager:
    def __init__(self, file_path):
        self.values = EasyDict()
        if file_path:
            self.file_path = file_path
            self.reload()
    
    def reload(self):
        self.clear()
        if self.file_path:
            with open(self.file_path, 'r') as f:
                self.values.update(json.load(f))
    
    def clear(self):
        self.values.clear()

    def update(self, in_dict):
        for (k1, v1) in in_dict.items():
            self.values[k1] = v1
    
    def export(self, save_file_name):
        if save_file_name:
            with open(save_file_name, 'w') as f:
                json.dump(dict(self.values), f)


def load_settings():
    try:
        conf = JsonConfigFileManager(SETTINGS_FN)
    except FileNotFoundError:
        with open(SETTINGS_FN, 'w') as f:
            empty_conf_object = {
                            "page_url": "",
                            "episode_part": 0,
                            "episode_num": 0,
                            "played_time": "0: 0",
                            "resting_term": 0,
                            "sound_volume": 100,
                        }
            empty_conf_string = json.dumps(empty_conf_object, indent=1)
            f.write(empty_conf_string)

        print("[x] Please set a " + SETTINGS_FN)
        sys.exit(0)

    return conf

def save_settings(conf, update_data):
    conf.update(update_data)
    conf.export(SETTINGS_FN)


if __name__ == "__main__":
    # Load Settings
    conf = load_settings()
    if not conf.values["page_url"]:
        print("[x] Please set a " + SETTINGS_FN)
        sys.exit(0)

    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-loggin"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches" , ["enable-automation"])

    # Connect page
    if getattr(sys, 'frozen', False):
        chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
        driver = webdriver.Chrome(executable_path=chromedriver_path, chrome_options=options)
    else:
        driver = webdriver.Chrome(executable_path="chromedriver", chrome_options=options)
    driver.get(url=conf.values["page_url"])
    driver.implicitly_wait(10)

    while(True):
        # Initial Scrolling for load
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Search the location of the video
        video_iframe_indexs = list()
        iframes = driver.find_elements_by_tag_name('iframe')
        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to_frame(iframes[i])
                iframe_title = driver.find_element_by_xpath('/html')
                if iframe_title.get_attribute("class") == "js-focus-visible":
                    video_iframe_indexs.append(i)

                driver.switch_to_default_content()
            except Exception as e:
                driver.switch_to_default_content()

        video_cnt = len(video_iframe_indexs)
        if VIDEO_MAX != video_cnt:
            print("[-] The Number of Videos is not " + str(VIDEO_MAX) + ". (" + str(video_cnt) + ")")
            sys.exit(0)

        # Play video start point to end
        start_episode_part = conf.values["episode_part"]
        for i in range(start_episode_part - 1, VIDEO_MAX):
            # Save settings
            data = {
                "page_url": conf.values["page_url"],
                "episode_part": i+1,
                # TODO: Set episode_num
            }
            save_settings(conf, data)

            driver.switch_to_frame(iframes[video_iframe_indexs[i]])

            # Play the video
            btn_play = driver.find_element_by_xpath('//*[@id="customCover"]/button/span')
            action = ActionChains(driver)
            action.move_to_element(btn_play).perform()
            btn_play.click()

            # TODO: Select play time point
            
            # Fullscreen
            driver.implicitly_wait(3)
            btn_full = driver.find_element_by_xpath('//*[@id="fullscreenBtn"]')
            driver.execute_script("arguments[0].click();", btn_full)
            
            # TODO: Control Volume

            # Detect end time
            time_point = driver.find_element_by_xpath('//*[@id="playProgress"]')
            while(True):
                time.sleep(5)
                time_style = time_point.get_attribute("style")
                time_float = float(time_style[len("width: "): -2])
                
                # TODO: Set custom end time
                if time_float == 100:   
                    break

            # Next Video
            driver.execute_script("arguments[0].click();", btn_full)
            driver.switch_to_default_content()
        
        # Next Page
        next_page = driver.find_element_by_xpath('//*[@id="main"]/div/div[1]/ul/li/div/div/div[2]/div/p[32]/span/a')

        conf.values["episode_part"] = 1
        conf.values["page_url"] = next_page.text

        driver.execute_script("arguments[0].click();", next_page)
        time.sleep(5)
