from PyQt6 import QtWidgets
import platform
import json
import websocket
import requests


class DragDropLineEdit(QtWidgets.QLineEdit):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        file_paths = event.mimeData().text()
        file_path = file_paths.split('\n')[0]
        
        if platform.system() == "Windows":
            file_path = file_path.replace('file:///', '')
        file_path = file_path.replace('file://', '', 1)
        
        self.setText(file_path)


def read_url_list(file_path):
    """读取文件并返回有效的URL列表"""
    try:
        from pathlib import Path
        urls = set(Path(file_path).read_text().splitlines())
        return [
            url.strip() if url.strip().startswith(('http://', 'https://'))
            else f"http://{url.strip()}"
            for url in urls if len(url.strip()) > 1
        ]
    except Exception as e:
        print(f"Error reading URL file: {e}")
        return []


def create_websocket_connection():
    """创建WebSocket连接并返回连接对象"""
    try:
        response = requests.get('http://127.0.0.1:9222/json')
        response.raise_for_status()
        ws_url = response.json()[0].get('webSocketDebuggerUrl')
        return websocket.create_connection(ws_url)
    except Exception as e:
        print(f"CDP连接失败: {e}")
        raise


def execute_cdp_command(connection: websocket, command: dict):
    """执行CDP命令并返回响应"""
    connection.send(json.dumps(command))
    return json.loads(connection.recv())


def evaluate_expression(call_frame_id: str, expression: str):
    """在指定调用帧上执行JavaScript表达式"""
    try:
        conn = create_websocket_connection()
        command = {
            'method': 'Debugger.evaluateOnCallFrame',
            'id': 1,
            'params': {
                'callFrameId': call_frame_id,
                'expression': expression,
                'objectGroup': 'console',
                'includeCommandLineAPI': True,
            }
        }
        response = execute_cdp_command(conn, command)
        return response["result"]["result"]['value']
    except Exception as e:
        print(f"Expression evaluation failed: {e}")
        raise


if __name__ == '__main__':
    callFrameId = "2900017506043058386.3.0"
    expression = 'rsa.encrypt("admin")'
