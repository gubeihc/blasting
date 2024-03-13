# return top 10 用户名
import base64

from utlis.jscode import performjs_code


def returndictionary(name):
    dictionary = {
        "用户名_top10": ['admin', 'administorator', 'test', 'root', 'guest', 'user', '1', 'test1', 'ADMIN', 'ROOT'],
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
        "用户名数字_1-100": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                             26,
                             27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
                             50,
                             51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73,
                             74,
                             75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97,
                             98,
                             99, 100],
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
        "密码数字_1-100": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                           26, 27,
                           28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
                           51,
                           52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
                           75,
                           76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98,
                           99,
                           100],
    }
    return dictionary[name]


def decode_base64(base64_string):
    # 添加适当数量的填充字符"="
    padding = len(base64_string) % 4
    if padding != 0:
        base64_string += "=" * (4 - padding)

    # 解码Base64字符串
    try:
        decoded_data = base64.b64decode(base64_string)
        return decoded_data
    except base64.binascii.Error:
        print("Invalid Base64 string")
        return None


async def return_code(imageslist, ocr, page_two_zd):
    codestr = ''
    for img in imageslist:
        yzm = img.replace('..', '').replace("//", "/")
        data = yzm.split(",")[1] if yzm.startswith("data:image") else \
            (await performjs_code(page_two_zd, yzm)).split(",")[1]
        try:
            code = ocr.classification(decode_base64(data))
            if len(code) == 4 or (6 > len(code) > 3):
                codestr = code
        except Exception as e:
            pass
    return codestr if codestr else "error"


if __name__ == '__main__':
    base64_string = "SGVsbG8gd29ybGQ="
    decoded_data = decode_base64(base64_string)
    if decoded_data:
        print(decoded_data.decode("utf-8"))
