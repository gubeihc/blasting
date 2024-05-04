import json
import aiohttp
import asyncio
import re
from PyQt6.QtCore import pyqtSignal, QObject


async def js_images_time(page_two):
    """
    触发网站img标签下 验证码的点击事件，确保jpg等图片后面跟上 时间戳，并对每一个图片设置跨域防止请求错误。
    :param page_two: 浏览器界面
    :return:
   """
    return await page_two.evaluate(
        '''()=>{
const images = document.getElementsByTagName('img');

for (let i = 0; i < images.length; i++) {
images[i].setAttribute('crossorigin', 'anonymous')

  images[i].addEventListener('click', function() {
    console.log('Image clicked!');
  });

  const clickEvent = new Event('click');
  images[i].dispatchEvent(clickEvent);
}

        }'''
    )


async def performjs_code(page_two, yzm):
    return await page_two.evaluate('''()=>{
                               
                               var arrImg = document.images;
                                 var datatext=''
                            var canvas = document.createElement("canvas");
                              var ctx = canvas.getContext("2d");
                                 for (let i = 0; i < arrImg.length; i++){
                                 if (arrImg[i].src.includes('%s')) {
                                 canvas.width = arrImg[i].width;
                                  canvas.height = arrImg[i].height;
                                 ctx.drawImage(arrImg[i],0,0,arrImg[i].width, arrImg[i].height);
                                 datatext = arrImg[i].src.substring(arrImg[i].src.lastIndexOf(".") + 1).toLowerCase()
                                 var dataURL = canvas.toDataURL("image/" + datatext)
                                console.log(dataURL)
                                 }
                                 }
                                 return dataURL
                                 }
                                 '''
                                   % yzm)


async def performjs(page_two, passwd, user):
    return await page_two.evaluate('''()=>{
const urls = [];
let username = '';
let password = '';
const forms = document.getElementsByTagName('input');
const checkboxes = [];

for (let i = 0; i < forms.length; i++) {
  if (forms[i].type === 'password') {
    password = '%s';
    forms[i].setAttribute("value",password);
    forms[i].dispatchEvent( new Event('change', { bubbles: true }));
    forms[i].dispatchEvent( new Event('input', { bubbles: true }));

    const prevIndex = i - 1;
    username = '%s';
    forms[prevIndex].setAttribute("value",username);
    forms[prevIndex].dispatchEvent( new Event('change', { bubbles: true }));
    forms[prevIndex].dispatchEvent( new Event('input', { bubbles: true }));

  } else if (forms[i].type === 'checkbox') {
    checkboxes.push(forms[i]);
  } else if (['submit', 'image', 'button'].includes(forms[i].type)) {
    forms[i].dispatchEvent(new CustomEvent('input'));
    if (forms[i].style.display === 'none') {
      continue;
    }
    forms[i].click();
    urls.push('isok');
  }
}

if (urls.length === 0) {
  const buttonForm = document.getElementsByTagName('button');
  if (buttonForm.length > 0) {
      urls.push('isok');
    buttonForm[0].click();
    console.log('js input 输入没找到 采用button提交 ');
  }
}

return urls;
                                                        }''' % (passwd, user))


async def performjs_yzm_code(page_two, passwd, user, code):
    return await page_two.evaluate('''()=>{
const urls = [];
let username = '';
let password = '';

const forms = document.getElementsByTagName('input');
for (let i = 0; i < forms.length; i++) {
  if (forms[i].type === 'password') {
    password = '%s';
    forms[i].setAttribute("value",password);
    forms[i].dispatchEvent( new Event('change', { bubbles: true }));
    forms[i].dispatchEvent( new Event('input', { bubbles: true }));
    // 获取用户名并存储到变量 username 中
    const prevIndex = i - 1;
    username = '%s';
    forms[prevIndex].setAttribute("value",username);
    forms[prevIndex].dispatchEvent( new Event('change', { bubbles: true }));
    forms[prevIndex].dispatchEvent( new Event('input', { bubbles: true }));


    const nextIndex = i + 1;
    yanzm = '%s'

    setTimeout(() => {
            forms[nextIndex].dispatchEvent(new Event('change', { bubbles: true }));
            forms[nextIndex].setAttribute("value", yanzm);
            forms[nextIndex].dispatchEvent(new Event('input', { bubbles: true }));
        }, 10);
    
  } else if (forms[i].type === 'checkbox' && !forms[i].checked) {
  setTimeout(() => {
               forms[i].click();
        }, 10);
  } else if (['submit', 'image', 'button'].includes(forms[i].type)) {
      setTimeout(() => {
    urls.push({username, password});
    forms[i].click();
        }, 10);
  }
}
if (urls.length === 0) {
  const buttonForm = document.getElementsByTagName('button');
  if (buttonForm.length > 0) {
        setTimeout(() => {
  urls.push('isok');
    buttonForm[0].click();
    console.log('js input 输入没找到button 通过 ');
        }, 10);
  }
      
  }
}
return urls;

                                                                    }''' % (passwd, user, code))


async def jsrequest(page_two, namepath, passpath, user, passwd, loginpath):
    return await page_two.evaluate('''()=>{

    function x(xpath) {
       var result = document.evaluate(xpath, document, null, XPathResult.ANY_TYPE, null);
       return result.iterateNext()
     };

                 var username = x('%s');
                 var password = x('%s');
                 
                 username.setAttribute("value",'%s');
                 username.dispatchEvent( new Event('change', { bubbles: true }));
                 username.dispatchEvent( new Event('input', { bubbles: true }));
                                  
                 password.setAttribute("value",'%s');
                 password.dispatchEvent( new Event('change', { bubbles: true }));
                 password.dispatchEvent( new Event('input', { bubbles: true }));
                 var but = x('%s');
                 but.click();
                                                                                 }''' % (
        namepath, passpath, user, passwd, loginpath))


async def jsrequest_code(page_two, namepath, passpath, codepath, user, passwd, code, loginpath):
    return await page_two.evaluate('''()=>{

            function x(xpath) {
           var result = document.evaluate(xpath, document, null, XPathResult.ANY_TYPE, null);
           return result.iterateNext()
         }

                     var username = x('%s');
                     var password = x('%s');
                     var yzm = x('%s');
                     
                username.setAttribute("value",'%s');
                 username.dispatchEvent( new Event('change', { bubbles: true }));
                 username.dispatchEvent( new Event('input', { bubbles: true }));
                                  
                 password.setAttribute("value",'%s');
                 password.dispatchEvent( new Event('change', { bubbles: true }));
                 password.dispatchEvent( new Event('input', { bubbles: true }));
                
                   setTimeout(() => {
                yzm.setAttribute("value",'%s');
                 yzm.dispatchEvent( new Event('change', { bubbles: true }));
                 yzm.dispatchEvent( new Event('input', { bubbles: true }));
        }, 10);
           setTimeout(() => {
                var but = x('%s')
                     but.click()
        }, 10);
               
                     
                                                                                     }''' % (
        namepath, passpath, codepath, user, passwd, code, loginpath))


class httpRaw(QObject):
    update_date = pyqtSignal(str)
    sem = asyncio.Semaphore(10)
    proxy = 'http://127.0.0.1:8080'
    datalist = []
    canshu = []

    # noinspection PyUnresolvedReferences
    async def post_req(self, path, header, datastr, ca):
        url = header.get("Host").strip()
        urls = "http://" + url + path
        async with self.sem:
            async with aiohttp.ClientSession(headers=header) as session:
                try:
                    if "application/json" in header.get("Content-Type"):
                        print("json")
                        print(datastr)
                        async with session.post(urls, ssl=False, json=datastr,
                                                proxy=self.proxy) as resp:
                            html = await resp.text()
                            title = await self.titles(html)
                            print(resp.status, resp.url, len(html))
                            self.update_date.emit(
                                f"status: {resp.status} url: {resp.url} title: {title} len: {len(html)} 参数: {ca}")
                    else:
                        async with session.post(urls, ssl=False, data=datastr,
                                                proxy=self.proxy) as resp:
                            html = await resp.text()
                            title = await self.titles(html)
                            print(resp.status, resp.url, len(html))
                            # noinspection PyUnresolvedReferences
                            self.update_date.emit(
                                f"status: {resp.status} url: {resp.url} title: {title} len: {len(html)} 参数: {ca}")

                        # result
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
                # noinspection PyBroadException
                try:
                    k, v = p.split(': ')
                    d[k] = v
                except Exception as e:
                    print(e)
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
                    print(e)
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
                    print(e)
            return path, d

    async def rundatalist(self):
        result = []
        for value, ca in zip(self.datalist, self.canshu):
            path, headers, data = self.parser_raw(value)
            result.append(asyncio.create_task(self.post_req(path, headers, data, ca)))
        await asyncio.wait(result)


if __name__ == '__main__':
    pass
