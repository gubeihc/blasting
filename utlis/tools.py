# 常用用户名和密码字典
import base64
from typing import Dict, List, Union, Optional

from utlis.jscode import performjs_code


def get_common_credentials(category: str) -> List[Union[str, int]]:
    """
    获取预定义的用户名和密码列表
    
    参数:
        category: 凭证类别名称
        
    返回值:
        返回指定类别的凭证列表
    """
    credentials: Dict[str, List[Union[str, int]]] = {
        "用户名_top10": ['admin', 'administrator', 'test', 'root', 'guest', 
                          'user', '1', 'test1', 'ADMIN', 'ROOT'],
        "用户名_top100": ['li', 'wang', 'zhang', 'liu', 'chen', 'yang', 'zhao', 'huang', 'zhou', 'wu', 'xu', 'sun',
                          'hu',
                          'zhu', 'gao', 'lin', 'he', 'guo', 'ma', 'luo', 'liang', 'song', 'zheng', 'xie', 'han', 'tang',
                          'feng', 'yu', 'dong', 'xiao', 'cheng', 'cao', 'yuan', 'deng', 'fu', 'shen', 'ceng', 'peng',
                          'lü', 'su', 'lu', 'jiang', 'cai', 'jia', 'ding', 'wei', 'xue', 'ye', 'yan', 'pan', 'du',
                          'dai',
                          'xia', 'zhong', 'tian', 'ren', 'fan', 'fang', 'shi', 'yao', 'tan', 'liao', 'zou', 'xiong',
                          'jin', 'hao', 'kong', 'bai', 'cui', 'kang', 'mao', 'qiu', 'qin', 'gu', 'hou', 'shao', 'meng',
                          'long', 'wan', 'duan', 'qian', 'yin', 'yi', 'chang', 'qiao', 'lai', 'gong', 'wen', 'pang',
                          'lan', 'tao', 'hong', 'zhai', 'an', 'ni', 'niu', 'ji', 'ge', 'you', 'bi'],
        "用户名数字_1-100": list(range(1, 101)),
        "弱口令_top10": ['123456789', 'admin', 'admin123', '123456', 'root', '12345678', 'test', 'admin@123', 'guest',
                         'adminstrator'],
        "弱口令_top100": ['123456', 'password', '12345678', '1234', 'admin@123', 'pussy', '12345', 'dragon', 'qwerty',
                          '696969', 'mustang', 'letmein', 'baseball', 'master', 'michael', 'football', 'shadow',
                          'monkey', 'abc123', 'pass', 'fuckme', '6969', 'jordan', 'harley', 'ranger', 'iwantu',
                          'jennifer', 'hunter', 'fuck', '2000', 'test', 'batman', 'trustno1', 'thomas', 'tigger',
                          'robert', 'access', 'love', 'buster', '1234567', 'soccer', 'hockey', 'killer', 'george',
                          'sexy', 'andrew', 'charlie', 'superman', 'asshole', 'fuckyou', 'dallas', 'jessica',
                          'panties', 'pepper', '1111', 'austin', 'william', 'daniel', 'golfer', 'summer', 'heather',
                          'hammer', 'yankees', 'joshua', 'maggie', 'biteme', 'enter', 'ashley', 'thunder', 'cowboy',
                          'silver', 'richard', 'fucker', 'orange', 'merlin', 'michelle', 'corvette', 'bigdog',
                          'cheese', 'matthew', '121212', 'patrick', 'martin', 'freedom', 'ginger', 'blowjob',
                          'nicole', 'sparky', 'yellow', 'camaro', 'secret', 'dick', 'falcon', 'taylor', '111111',
                          '131313', '123123', 'bitch', 'hello', 'scooter'],
        "密码数字_1-100": list(range(1, 101)),
    }
    return credentials.get(category, [])


def decode_base64_safe(base64_string: str) -> Optional[bytes]:
    """
    安全地解码base64字符串，自动处理填充字符
    
    参数:
        base64_string: 需要解码的base64编码字符串
        
    返回值:
        解码后的字节数据，解码失败则返回None
    """
    try:
        # 添加必要的填充字符
        padding = len(base64_string) % 4
        if padding:
            base64_string += "=" * (4 - padding)
            
        return base64.b64decode(base64_string)
    except (TypeError, ValueError, base64.binascii.Error) as e:
        print(e)
        # TypeError: 输入不是字符串
        # ValueError: 非法字符
        # binascii.Error: 非法的base64编码
        return None


from typing import List, Optional, Any


async def extract_verification_code(
        image_sources: List[str],  # 更清晰的参数类型
        ocr_engine: Any,
        page_context: Any
) -> str:
    """
    从图片源中提取验证码

    Args:
        image_sources: 图片路径或 Base64 编码的图片列表
        ocr_engine: OCR 引擎实例
        page_context: 页面上下文对象

    Returns:
        str: 提取的验证码，失败返回 "error"
    """
    for img in image_sources:
        data = await get_image_base64(img, page_context)
        if not data:
            continue

        try:
            code = ocr_engine.classification(decode_base64_safe(data))
            if is_valid_verification_code(code):
                return code
        except Exception:
            continue

    return "error"


async def get_image_base64(image_source: str, page_context: Any) -> Optional[str]:
    """从图片源获取 Base64 编码数据"""
    image_path = image_source.replace("..", "")

    if image_path.startswith("data:image"):
        parts = image_path.split(",", 1)
        return parts[1] if len(parts) > 1 else None

    js_result = await performjs_code(page_context, image_path)
    if js_result and "," in js_result:
        return js_result.split(",", 1)[1]

    return None


def is_valid_verification_code(code: str) -> bool:
    """验证码有效性检查"""
    return 4 <= len(code) <= 5


if __name__ == '__main__':
    # 测试base64解码
    test_string = "SGVsbG8gd29ybGQ="
    decoded = decode_base64_safe(test_string)
    if decoded:
        print(decoded.decode("utf-8"))
