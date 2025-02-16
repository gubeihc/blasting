import json
import aiohttp
import asyncio
import re
from typing import Optional, Dict, Any, List, Tuple
from PyQt6.QtCore import pyqtSignal, QObject

# JavaScript 模板常量
JS_IMAGE_HANDLER = """
() => {
    // 处理所有图片
    const images = document.getElementsByTagName('img');
    for (let img of images) {
        img.setAttribute('crossorigin', 'anonymous');
        img.addEventListener('click', () => console.log('Image clicked!'));
        img.dispatchEvent(new Event('click'));
    }

    // 处理所有 checkbox
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    for (let checkbox of checkboxes) {
        checkbox.addEventListener('click', () => console.log('Checkbox clicked!'));
        checkbox.checked = !checkbox.checked; // 切换选中状态
        checkbox.dispatchEvent(new Event('click'));
    }
}
"""

JS_CANVAS_TEMPLATE = """
() => {
    const arrImg = document.images;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    
    for (const img of arrImg) {
        if (img.src.includes('%s')) {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0, img.width, img.height);
            const format = img.src.substring(img.src.lastIndexOf(".") + 1).toLowerCase();
            return canvas.toDataURL("image/" + format);
        }
    }
    return null;
}
"""

JS_LOGIN_TEMPLATE = """
() => {
    const urls = [];
    const forms = document.getElementsByTagName('input');
    
    for (let i = 0; i < forms.length; i++) {
        if (forms[i].type === 'password') {
            // 设置密码
            forms[i].setAttribute("value", '%s');
            forms[i].dispatchEvent(new Event('change', { bubbles: true }));
            forms[i].dispatchEvent(new Event('input', { bubbles: true }));

            // 设置用户名
            const prevIndex = i - 1;
            forms[prevIndex].setAttribute("value", '%s');
            forms[prevIndex].dispatchEvent(new Event('change', { bubbles: true }));
            forms[prevIndex].dispatchEvent(new Event('input', { bubbles: true }));
        } else if (['submit', 'image', 'button'].includes(forms[i].type)) {
            if (forms[i].style.display !== 'none') {
                forms[i].dispatchEvent(new CustomEvent('input'));
                forms[i].click();
                urls.push('isok');
            }
        }
    }

    // 尝试使用 button 提交
    if (urls.length === 0) {
        const buttonForm = document.getElementsByTagName('button');
        if (buttonForm.length > 0) {
            buttonForm[0].click();
            urls.push('isok');
        }
    }

    return urls;
}
"""

JS_LOGIN_WITH_CODE_TEMPLATE = """
() => {
// 处理所有 checkbox
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    for (let checkbox of checkboxes) {
        checkbox.addEventListener('click', () => console.log('Checkbox clicked!'));
        checkbox.checked = !checkbox.checked; // 切换选中状态
        checkbox.dispatchEvent(new Event('click'));
    }
    const xpath = (path) => {
        const result = document.evaluate(
            path, 
            document, 
            null, 
            XPathResult.ANY_TYPE, 
            null
        );
        return result.iterateNext();
    };

    const dispatchEvents = (element, value) => {
        element.setAttribute("value", value);
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new Event('input', { bubbles: true }));
    };

    // 获取元素
    const username = xpath('%s');
    const password = xpath('%s');
    const yzm = xpath('%s');
    const submitButton = xpath('%s');

    // 设置用户名和密码
    dispatchEvents(username, '%s');
    dispatchEvents(password, '%s');

    // 设置验证码并提交
    setTimeout(() => {
        dispatchEvents(yzm, '%s');
        setTimeout(() => submitButton.click(), 10);
    }, 10);
}
"""



async def js_images_time(page_two) -> None:
    """处理页面图片元素，设置跨域属性并触发点击事件"""
    await page_two.evaluate(JS_IMAGE_HANDLER)

async def performjs_code(page_two: Any, yzm: str) -> Optional[str]:
    """处理验证码图片并返回 base64 编码"""
    try:
        return await page_two.evaluate(JS_CANVAS_TEMPLATE % yzm)
    except Exception as e:
        print(f"验证码处理失败: {e}")
        return None

async def performjs(page_two, passwd: str, user: str) -> List[str]:
    """
    执行登录表单填充和提交
    
    Args:
        page_two: 页面对象
        passwd: 密码
        user: 用户名
    
    Returns:
        List[str]: 提交状态列表
    """
    return await page_two.evaluate(JS_LOGIN_TEMPLATE % (passwd, user))

async def performjs_yzm_code(page_two, passwd, user, code):
    """
    执行带验证码的登录表单填充和提交
    
    Args:
        page_two: 页面对象
        passwd: 密码
        user: 用户名
        code: 验证码
    
    Returns:
        Dict: 包含提交状态和详细信息的字典
    """
    return await page_two.evaluate('''() => {
        const result = {
            status: false,
            message: '',
            details: {}
        };

        const forms = document.getElementsByTagName('input');
        for (let i = 0; i < forms.length; i++) {
            if (forms[i].type === 'password') {
                // 设置密码
                forms[i].setAttribute("value", '%s');
                forms[i].dispatchEvent(new Event('change', { bubbles: true }));
                forms[i].dispatchEvent(new Event('input', { bubbles: true }));
                
                // 设置用户名
                const prevIndex = i - 1;
                forms[prevIndex].setAttribute("value", '%s');
                forms[prevIndex].dispatchEvent(new Event('change', { bubbles: true }));
                forms[prevIndex].dispatchEvent(new Event('input', { bubbles: true }));

                // 设置验证码
                const nextIndex = i + 1;
                forms[nextIndex].setAttribute("value", '%s');
                forms[nextIndex].dispatchEvent(new Event('change', { bubbles: true }));
                forms[nextIndex].dispatchEvent(new Event('input', { bubbles: true }));

                result.details = {
                    username: '%s',
                    hasPassword: true,
                    hasCode: true
                };
            }
        }

        // 提交表单
        const submitButton = Array.from(forms).find(form => 
            ['submit', 'image', 'button'].includes(form.type)
        );
        
        if (submitButton) {
            submitButton.click();
            result.status = true;
            result.message = '表单提交成功';
        } else {
            // 尝试使用button标签提交
            const buttonForm = document.getElementsByTagName('button')[0];
            if (buttonForm) {
                buttonForm.click();
                result.status = true;
                result.message = '通过button标签提交成功';
            } else {
                result.message = '未找到提交按钮';
            }
        }

        return result;
    }''' % (passwd, user, code, user))



async def jsrequest(
    page_two: Any,
    namepath: str,
    passpath: str,
    user: str,
    passwd: str,
    loginpath: str
) -> None:
    """
    执行基本的登录表单填充和提交
    
    Args:
        page_two: 页面对象
        namepath: 用户名输入框的XPath
        passpath: 密码输入框的XPath
        user: 用户名
        passwd: 密码
        loginpath: 提交按钮的XPath
    """
    return await page_two.evaluate('''() => {
    // 处理所有 checkbox
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    for (let checkbox of checkboxes) {
        checkbox.addEventListener('click', () => console.log('Checkbox clicked!'));
        checkbox.checked = !checkbox.checked; // 切换选中状态
        checkbox.dispatchEvent(new Event('click'));
    }
        function xpath(path) {
            const result = document.evaluate(
                path,
                document,
                null,
                XPathResult.ANY_TYPE,
                null
            );
            return result.iterateNext();
        }

        const username = xpath('%s');
        const password = xpath('%s');
        
        // 设置用户名
        username.setAttribute("value", '%s');
        username.dispatchEvent(new Event('change', { bubbles: true }));
        username.dispatchEvent(new Event('input', { bubbles: true }));
        
        // 设置密码
        password.setAttribute("value", '%s');
        password.dispatchEvent(new Event('change', { bubbles: true }));
        password.dispatchEvent(new Event('input', { bubbles: true }));
        
        // 点击提交按钮
        const submitButton = xpath('%s');
        submitButton.click();
    }''' % (namepath, passpath, user, passwd, loginpath))


async def jsrequest_code(
    page_two,
    namepath: str,
    passpath: str,
    codepath: str,
    user: str,
    passwd: str,
    code: str,
    loginpath: str
) -> None:
    """
    执行带验证码的登录表单填充和提交
    
    Args:
        page_two: 页面对象
        namepath: 用户名输入框的XPath
        passpath: 密码输入框的XPath
        codepath: 验证码输入框的XPath
        user: 用户名
        passwd: 密码
        code: 验证码
        loginpath: 提交按钮的XPath
    """
    return await page_two.evaluate(
        JS_LOGIN_WITH_CODE_TEMPLATE % (
            namepath, passpath, codepath, loginpath,
            user, passwd, code
        )
    )


class HTTPRaw(QObject):
    update_date = pyqtSignal(str)
    
    def __init__(self, max_concurrent: int = 10, proxy: str = 'http://127.0.0.1:8080'):
        super().__init__()
        self.sem = asyncio.Semaphore(max_concurrent)
        self.proxy = proxy
        self.datalist: List[str] = []
        self.canshu: List[str] = []

    async def _extract_title(self, html: str) -> Optional[str]:
        """从HTML中提取标题"""
        title_patterns = [
            r"<title name='school' class=\"i18n\">(.*?)</title>",
            r'document.title\s*=\s*"(.*?)"',
            r'<title>(.*?)</title>',
            r'<title t="(.*?)"></title>',
            r'<title class="next-head">(.*?)</title>',
            r'<h1 class="l logo">(.*?)</h1>',
        ]
        
        html = html.replace(' ', '')
        for pattern in title_patterns:
            if match := re.search(pattern, html, re.S | re.I):
                return match.group(1).strip()
        return None

    async def post_request(self, path: str, headers: Dict[str, str], 
                          data: Any, context: str) -> None:
        """发送POST请求并处理响应"""
        url = f"http://{headers.get('Host', '').strip()}{path}"
        
        async with self.sem:
            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    is_json = "application/json" in headers.get("Content-Type", "")
                    kwargs = {
                        'ssl': False,
                        'proxy': self.proxy,
                        'json' if is_json else 'data': data
                    }
                    
                    async with session.post(url, **kwargs) as resp:
                        html = await resp.text()
                        title = await self._extract_title(html)
                        
                        self.update_date.emit(
                            f"status: {resp.status} url: {resp.url} "
                            f"title: {title} len: {len(html)} 参数: {context}"
                        )
                        
            except Exception as e:
                print(f"Request error: {e}")

    def parse_raw_request(self, raw: str) -> Tuple[str, Dict[str, str], Any]:
        """解析原始HTTP请求"""
        lines = raw.split('\n')
        method, path, *_ = lines[0].split()
        
        # 解析headers
        headers = {}
        header_lines = [line.strip() for line in lines[1:] if ': ' in line]
        for line in header_lines:
            key, value = line.split(': ', 1)
            headers[key] = value

        # 处理POST数据
        if method == "POST":
            data_start = raw.index("\n\n") + 2
            data = raw[data_start:].strip()
            
            if "application/json" in headers.get("Content-Type", ""):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    print("Invalid JSON data")
                    
            return path, headers, data
            
        return path, headers, None

    async def run_requests(self) -> None:
        """批量执行请求"""
        tasks = []
        for raw_data, context in zip(self.datalist, self.canshu):
            try:
                path, headers, data = self.parse_raw_request(raw_data)
                task = self.post_request(path, headers, data, context)
                tasks.append(asyncio.create_task(task))
            except Exception as e:
                print(f"Error parsing request: {e}")
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    pass
