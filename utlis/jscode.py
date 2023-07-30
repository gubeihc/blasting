import json

import aiohttp
import asyncio
import re
from PyQt6.QtCore import pyqtSignal, QObject


async def performJs_yzm_code(page_two, passwd, user, code):
    return await page_two.evaluate('''()=>{
                                                var urls = [];
                                                var checkbox_list=[];
                                                let user='';
                                                let password='';
                                                let u;
                                                let c;
                                                let form = document.getElementsByTagName('input');
                                                for (let i = 0; i < form.length; i++) {
                                                    if (form[i].type == 'password') {
                                                        form[i].value = '%s'
                                                         password=form[i].value
                                                         form[i].dispatchEvent(new CustomEvent('input'))
                                                         u = i - 1
                                                         form[u].value = '%s'
                                                         form[u].dispatchEvent(new CustomEvent('input'))
                                                         username=form[u].value
                                                        c = i+1
                                                        form[c].value = '%s'
                                                         form[c].dispatchEvent(new CustomEvent('input'))

                                                    }
                                                    if (form[i].type == 'checkbox' && form[i].checked==false){
                                                     form[i].click()
                                     }
                                                    if (form[i].type == 'submit') {
                                                                urls.push(user,password)
                                                        form[i].click()
                                                    }
                                                    if (form[i].type=='image'){
                                                        urls.push(user,password)
                                                        form[i].click()
                                                    }
                                                     if (form[i].type=='button'){
                                                        urls.push(user,password)
                                                        form[i].click()
                                                    }

                                                }


                                                return urls;
                                                                    }''' % (passwd, user, code))


async def performjs_code(page_two, yzm):
    return await page_two.evaluate('''()=>{
                                 var arrImg = document.images;
                                 for (let i = 0; i < arrImg.length; i++){
                                 if (arrImg[i].src.includes('%s')) {
                                     var canvas = document.createElement("canvas");
                                     canvas.width = arrImg[i].width;
                                     canvas.height = arrImg[i].height;
                                     var ctx = canvas.getContext("2d");
                                     ctx.drawImage(arrImg[i], 0, 0, arrImg[i].width, arrImg[i].height);
                                     var ext = arrImg[i].src.substring(arrImg[i].src.lastIndexOf(".") + 1).toLowerCase();
                                     var dataURL = canvas.toDataURL("image/" + ext)
                                  }
                                 }
                                 return dataURL
                                 }
                                 '''
                                   % yzm)


async def performJs(page_two, passwd, user):
    return await page_two.evaluate('''()=>{
                                    var urls = [];
                                    var checkbox_list = [];
                                    let user='';
                                    let password='';
                                    let u;
                                    let form = document.getElementsByTagName('input');
                                    for (let i = 0; i < form.length; i++) {
                                        if (form[i].type == 'password') {
                                            form[i].value = '%s'
                                            password=form[i].value
                                            form[i].dispatchEvent(new CustomEvent('input'))
                                            u = i - 1
                                            form[u].value = '%s'
                                            form[u].dispatchEvent(new CustomEvent('input'))

                                            username=form[u].value
                                        }
                                        if (form[i].type == 'checkbox'){
                                             checkbox_list.push(form[i])
                                        }
                                        if (form[i].type == 'submit') {
                                                    urls.push(user,password)
                                            form[i].dispatchEvent(new CustomEvent('input'))

                                            form[i].click()
                                        }
                                        if (form[i].type=='image'){
                                            form[i].dispatchEvent(new CustomEvent('input'))

                                            urls.push(user,password)
                                            form[i].click()
                                        }
                                         if (form[i].type=='button'){
                                        form[i].dispatchEvent(new CustomEvent('input'))
                                            urls.push(user,password)
                                            form[i].click()
                                        }
                                    }
                                    for (let e = 0; e < checkbox_list.length; e++) {
                                             checkbox_list[e].click()

                                    }

                                    return urls;
                                                        }''' % (passwd, user))


async def jsRequest(page_two, namepath, passpath, user, passwd, loginpath):
    return await page_two.evaluate('''()=>{

                             function x(xpath) {
       var result = document.evaluate(xpath, document, null, XPathResult.ANY_TYPE, null);
       return result.iterateNext()
     };

                 var name = x('%s');
                 var password = x('%s');
                 name.value =  '%s';
                 password.value= '%s';
                 var but = x('%s');
                 but.click();
                                                                                 }''' % (
        namepath, passpath, user, passwd, loginpath))


async def jsRequest_code(page_two, namepath, passpath, codepath, user, passwd, code, loginpath):
    return await page_two.evaluate('''()=>{

                                 function x(xpath) {
           var result = document.evaluate(xpath, document, null, XPathResult.ANY_TYPE, null);
           return result.iterateNext()
         }

                     var name = x('%s');
                     var password = x('%s');
                     var yzm = x('%s');
                     name.value= '%s'
                     password.value =  '%s'
                     yzm.value =  '%s'
                     var but = x('%s')
                     but.click()
                                                                                     }''' % (
        namepath, passpath, codepath, user, passwd, code, loginpath))

    # 判断url是否爆破成功


class httpRaw(QObject):
    update_date = pyqtSignal(str)
    sem = asyncio.Semaphore(10)
    proxy = 'http://127.0.0.1:8080'
    datalist = []
    canshu = []

    async def post_req(self, path, header, data, ca):
        url = header.get("Host").strip()
        urls = "http://" + url + path
        async with self.sem:
            async with aiohttp.ClientSession(headers=header) as session:
                try:
                    if "application/json" in header.get("Content-Type"):
                        print("json")
                        print(data)
                        async with session.post(urls, ssl=False, json=data,
                                                proxy=self.proxy) as resp:
                            html = await resp.text()
                            title = await self.titles(html)
                            print(resp.status, resp.url, len(html))
                            self.update_date.emit(
                                f"status: {resp.status} url: {resp.url} title: {title} len: {len(html)} 参数: {ca}")
                    else:
                        async with session.post(urls, ssl=False, data=data,
                                                proxy=self.proxy) as resp:
                            html = await resp.text()
                            title = await self.titles(html)
                            print(resp.status, resp.url, len(html))
                            self.update_date.emit(
                                f"status: {resp.status} url: {resp.url} title: {title} len: {len(html)} 参数: {ca}")

                        # result
                except Exception as e:
                    print(e)

    #
    async def get_req(self, path, header):
        urls = header.get("Host").strip()
        url = "http://" + urls + path
        print(url)
        async with aiohttp.ClientSession(headers=header) as session:
            try:
                # async with session.get("https://www.baidu.com", ssl=False) as resp:
                async with session.get(url, ssl=False) as resp:
                    print(resp.status, resp.url, len(await resp.text()))
                    print("=======" * 10)
                    print(await resp.text())
            except Exception as e:
                print(e)

    async def titles(self, html):
        titles = (
            "<titlename='school'class=\"i18n\">(.*)</title>",
            'document.title\s=\s"(.*?)"',
            'document.title="(.*?)"',
            '<title>(.*?)</title>',
            '<titlet="(.*?)"></title>',
            '<title class="next-head">(.*?)</title>',
            '<h1 class="l logo">(.*)</h1>',
        )
        html = html.replace(' ', '')
        for ti in titles:
            title = re.findall(ti, html, re.S | re.I)
            if len(title) == 0:
                continue
            elif len(title) >= 1:
                if len(title[0]) >= 1:
                    data = str(title[0]).replace('\r', '').replace('\n', '').strip()
                    return data
                elif len(title) >= 2:
                    data = str(title[1]).replace('\r', '').replace('\n', '').strip()
                    return data

    def parser_raw(self, raw):
        mode = raw.split()[0]
        if mode == "POST" and "Content-Type: application/json" not in raw:
            path = raw.split()[1]
            data = raw.split()[-1]
            pairs = [p for p in raw.split('\n')[1:] if p.strip()]
            # 遍历每个键值对，将其按冒号分割，然后生成一个新的字典
            d = {}
            for p in pairs:
                try:
                    k, v = p.split(': ')
                    d[k] = v
                except Exception as e:
                    pass
            return path, d, data
        elif mode == "POST" and "Content-Type: application/json" in raw:
            data_start_index = raw.index(
                "\n\n") + 2
            data = raw[data_start_index:].strip()
            json_data = json.loads(data)
            path = raw.split()[1]
            pairs = [p for p in raw.split('\n')[1:] if p.strip()]
            # 遍历每个键值对，将其按冒号分割，然后生成一个新的字典
            d = {}
            for p in pairs:
                try:
                    k, v = p.split(': ')
                    d[k] = v
                except Exception as e:
                    pass
            return path, d, json_data
        elif mode == "GET":
            path = raw.split()[1]
            pairs = [p for p in raw.split('\n')[2:] if p.strip()]
            # 遍历每个键值对，将其按冒号分割，然后生成一个新的字典
            d = {}
            for p in pairs:
                try:
                    k, v = p.split(': ')
                    d[k] = v
                except Exception as e:
                    pass
            return path, d

    async def main(self):
        # http://172.81.234.61/
        raw = '''
POST /api/authentication/user/loginWithCaptcha HTTP/1.1
Host: www.baidu.com
Accept: application/json, text/plain, */*
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.62 Safari/537.36
Content-Type: application/json;charset=UTF-8
Origin: http://www.baidu.com
Referer: http://www.baidu.com
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: HWWAFSESID=28f1176cae42894b96; HWWAFSESTIME=1690296326365
Connection: close

{"captchaUuid":"bd8c0b104b454a38aa3cd4d65f041185","captchaValue":"155","loginName":"qwet","password":"3e744b9dc39389baf0c5a0660589b8402f3dbb49b89b3e75f2c9355852a3c677"}
        '''
        path, headrs, data = self.parser_raw(raw)
        await self.post_req(path, headrs, data, "test")

    async def rundatalist(self):
        result = []
        for value, ca in zip(self.datalist, self.canshu):
            path, headers, data = self.parser_raw(value)
            result.append(asyncio.create_task(self.post_req(path, headers, data, ca)))
        await asyncio.wait(result)


if __name__ == '__main__':
    data = httpRaw()
    asyncio.run(data.main())
