import os
import json
import copy
import re
import urllib
import requests
import execjs
from http.cookiejar import CookieJar
from bs4 import BeautifulSoup

JSFILE = "encrypt.js"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
checkinUrl = "http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.html"
hisUrl = "http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do"
loginUrl="https://authserver.nju.edu.cn/authserver/login?service=http%3A%2F%2Fehallapp.nju.edu.cn%2Fxgfw%2Fsys%2Fyqfxmrjkdkappnju%2Fapply%2FgetApplyInfoList.do"

UserAgent=   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"

HEADERS = {
    'User-Agent': UserAgent
}


class Njuer:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.cookies = CookieJar()

    def login(self):
        info = {
            "username": USERNAME,
            "password": PASSWORD,
        }
        checkinUrl = "http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.html"
        hisUrl = "http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do"
        loginUrl = "https://authserver.nju.edu.cn/authserver/login?service=http%3A%2F%2Fehallapp.nju.edu.cn%2Fxgfw%2Fsys%2Fyqfxmrjkdkappnju%2Fapply%2FgetApplyInfoList.do"

        self.session.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Mobile Safari/537.36"
        self.session.cookies = CookieJar()
        response = self.session.get(loginUrl)
        soup = BeautifulSoup(response.text, "lxml")

        inputs = soup.find_all("input")
        for i in inputs:
            if i.get("name") not in ["username", "password", "captchaResponse", ]:
                info[i.get("name")] = i.get("value")
        pattern = re.compile(r"var pwdDefaultEncryptSalt = (.*?);", re.MULTILINE | re.DOTALL)
        script = str(soup.find("script", text=pattern))
        pwdDefaultEncryptSalt = re.search('pwdDefaultEncryptSalt = "(.*?)";', script).group(1)
        print(pwdDefaultEncryptSalt)
        loginInfo = {
            'username': USERNAME,
            'password': self.exec_js_func(JSFILE, 'encryptAES', PASSWORD, pwdDefaultEncryptSalt),
            'captchaResponse': '',
            'lt': info["lt"],
            'dllt': info["dllt"],
            'execution': info["execution"],
            '_eventId': info["_eventId"],
            'rmShown': info["rmShown"]
        }
        print(loginInfo)
        data = urllib.parse.urlencode(loginInfo)
        headers = copy.deepcopy(HEADERS)
        headers.update({
            'Origin': "https://authserver.nju.edu.cn",
            'Referer': loginUrl,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        self.session.post(loginUrl, data=data, headers=headers)
        return

    def exec_js_func(self, js_file, func, *params):
        with open(js_file, 'r') as f:
            lines = f.readlines()
        js = ''.join(lines)
        js_context = execjs.compile(js)
        result = js_context.call(func, *params)
        return result

    def getCheckInfo(self):
        res = self.session.get(hisUrl)
        resJson = json.loads(res.text)
        wid = resJson['data'][0]['WID']
        hisLoc =resJson['data'][1]['CURR_LOCATION']
        return {'hisLoc':hisLoc,'wid':wid}

    def checkin(self):
        info = '&IS_TWZC=1&IS_HAS_JKQK=1&JRSKMYS=1&JZRJRSKMYS=1'  # 分别对应四个单选框的值
        link = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do?WID={wid}&CURR_LOCATION={curr_location}'
        hisInfo = self.getCheckInfo()
        link = link.format(wid=str(hisInfo['wid']), curr_location=str(hisInfo['hisLoc']) + info)
        res = self.session.get(link)
        res = json.loads(res.text)
        if res['code'] == '0':
            if res['msg'] == '成功':
                print('打卡成功')
                return 1
        print('打卡失败')
        return 0

if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("请正确配置用户名和密码！")
        sys.exit()
    try：

        bot = Njuer(USERNAME, PASSWORD)
        bot.login()
        bot.checkin()
        
    except Exception as e:
        print("打卡失败，请手动打卡", str(e))
