__title__ = 'poly_bulletin.py'
__doc__ = 'Check the Polytechnique Montreal student dossier on a regular basis for changes in final grades.'
__author__ = 'BENABBOU, Younes.'

import aspose.words as aw
import time
import os
import configparser
from datetime import date
from taste_the_rainbow import *

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException


CATEGORY = "Poly_Bulletin"
CONFIG_LOC = 'Login.cfg'
BULLETIN_PATH = os.path.dirname(os.path.abspath(__file__)) + r"\Bulletin"


############################################################################################################

#                                     Get Login credentials                                                #
############################################################################################################

def get_config(section: str, values: list[str]) -> list[str]:
    assert os.path.exists(CONFIG_LOC), "Missing login info file"
    config = configparser.ConfigParser()
    config.read(CONFIG_LOC)
    return [config.get(section, x) for x in values]

def get_login_info() -> None:
    global CODE, NIP, NAISSANCE, EMAIL
    CODE, NIP, NAISSANCE, EMAIL = get_config(
        'Poly', ['code', 'nip', 'naissance', 'email'])
    return

############################################################################################################

#                                     Log to DOSSIER ETUDIANT and download Bulletin                        #
############################################################################################################

def get_bulletin() -> None:
    url = '''https://dossieretudiant.polymtl.ca/WebEtudiant7/poly.html'''
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_argument("--log-level=3")  # delete in case of error
    options.add_experimental_option(
        'excludeSwitches', ['enable-logging'])  # disable DevTools logging
    options.add_experimental_option('prefs', {
        "download.default_directory": BULLETIN_PATH,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options, service_log_path=None)
    driver.get(url)

    code_input = driver.find_element(By.ID, "code")
    code_input.send_keys(CODE)

    nip_input = driver.find_element(By.ID, "nip")
    nip_input.send_keys(NIP)

    naissance_input = driver.find_element(By.ID, "naissance")
    naissance_input.send_keys(NAISSANCE)

    login_btn = driver.find_element(
        By.XPATH, '/html/body/div[2]/div[2]/form/div[4]/input')
    login_btn.click()
    
    time.sleep(10)

    bulletin_btn = driver.find_element(By.NAME, "btnBulCumul")
    bulletin_btn.click()

    time.sleep(10)

    driver.close()

    os.rename(BULLETIN_PATH +
            f"\\{os.listdir(BULLETIN_PATH)[0]}", BULLETIN_PATH + r"\new.pdf")

    return

############################################################################################################

#                                     Compare Pdfs                                                         #
############################################################################################################

def compare_pdfs(fileName1: str, fileName2: str) -> bool:
    pdf1 = aw.Document(fileName1)
    pdf2 = aw.Document(fileName2)

    pdf1.accept_all_revisions()
    pdf2.accept_all_revisions()

    options = aw.comparing.CompareOptions()
    options.ignore_formatting = True
    options.ignore_headers_and_footers = True
    options.ignore_case_changes = True
    options.ignore_tables = True
    options.ignore_fields = True
    options.ignore_comments = True
    options.ignore_textboxes = True
    options.ignore_footnotes = True

    pdf1.compare(pdf2, "user", date.today(), options)

    return pdf1.revisions.count > 0

############################################################################################################

#                                     Send Email in case of an update                                      #
############################################################################################################

def send() -> None:
    url = '''https://www.imp.polymtl.ca/login.php'''
    path = BULLETIN_PATH + r"\\bulletin.pdf"
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_experimental_option(
        'excludeSwitches', ['enable-logging'])  # disable DevTools logging
    options.add_argument("--log-level=3")  # delete in case of error

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    user_input = driver.find_element(By.ID, "horde_user")
    user_input.send_keys(CODE)

    password_input = driver.find_element(By.ID, "horde_pass")
    password_input.send_keys(NIP)

    login_btn = driver.find_element(By.ID, "login-button")
    login_btn.click()

    new_mail_btn = driver.find_element(By.ID, "composelink")
    new_mail_btn.click()

    driver.switch_to.window(driver.window_handles[-1])

    email_input = driver.find_element(
        By.XPATH, "/html/body/div[3]/form/div[2]/div[1]/table/tbody/tr[1]/td[2]/div/ul/li/input")
    email_input.send_keys(EMAIL)

    subject_input = driver.find_element(By.ID, "subject")
    subject_input.send_keys("Bulletin Update")

    upload_input = driver.find_element(By.ID, "upload")
    upload_input.send_keys(path)

    text_input = driver.find_element(By.ID, "composeMessage")
    text_input.send_keys(
        '''Hello,\nYou will find your bulletin attached down below.''')

    time.sleep(10)

    send_btn = driver.find_element(By.ID, "send_button")
    send_btn.click()

    time.sleep(10)

    driver.close()

    return

############################################################################################################

#                           Initialization of old Pdf if it doesn't exist                                  #
############################################################################################################

def init() -> None:
    if not(os.path.exists(BULLETIN_PATH)):
        os.mkdir(BULLETIN_PATH)
    elif len(os.listdir(BULLETIN_PATH)) > 1:
        files = os.listdir(BULLETIN_PATH)
        
        for file in files:
            if file != "old.pdf":
                os.remove(BULLETIN_PATH + f"\\{file}")
                
        return
    elif os.listdir(BULLETIN_PATH)[0] != "old.pdf":
        os.remove(BULLETIN_PATH + f"/{os.listdir(BULLETIN_PATH)[0]}")
    else:
        return
    
    get_bulletin()
    os.rename(BULLETIN_PATH +
            f"\\{os.listdir(BULLETIN_PATH)[0]}", BULLETIN_PATH + r"\old.pdf")

    return

############################################################################################################

#                                    Main functions                                                        #
############################################################################################################

def check_final_grades() -> None:
    get_bulletin()
    different = compare_pdfs(r"Bulletin\old.pdf", r"Bulletin\new.pdf")
    if different:
        os.rename(
            BULLETIN_PATH + r"\new.pdf", BULLETIN_PATH + r"\bulletin.pdf")
        send()
        os.remove(r"Bulletin\old.pdf")
        os.rename(
                BULLETIN_PATH + f"\\{os.listdir(BULLETIN_PATH)[0]}", BULLETIN_PATH + r"\old.pdf")
        print_success(CATEGORY, f"UPDATE SENT to {EMAIL}")
    else:
        os.remove(r"Bulletin\new.pdf")
        print_no_change(CATEGORY, f"No update")

    return

def main_loop() -> None:
    try:
        print_header(CATEGORY, f"Initializing...")
        get_login_info()
        init()
        while True:
            print_header(
                CATEGORY, f"{time.ctime()} || Checking final grades for updates...")
            check_final_grades()
            # Wait 15 min
            print_sleeping(CATEGORY, f"Waiting for final grades...")
            time.sleep(900)
    except NoSuchElementException:
        print_failure(CATEGORY, "Incorrect login information!!!")
    except Exception as e:
        print_failure(CATEGORY, e.__str__())

    return

############################################################################################################
############################################################################################################

if __name__ == '__main__':
    main_loop()
