import json
import threading

import requests

from ton_config import TonUser


# 假设的login函数，实际应根据你的登录接口进行实现
def login(userId):
    payload = {
        "userId": userId
    }
    r = requests.post('https://apiv2.gabby.world/api/ton/auth/login1', json=payload, timeout=10)
    result = r.json()
    token = result.get('data').get('token')
    # 这里应该是调用登录接口的代码，以下为模拟过程
    print(f"正在登录用户ID: {userId}")
    # 模拟登录过程
    # print(f"用户ID: {userId} 的token为: {token}")
    return token


class UserIDGenerator:
    def __init__(self, start, end):
        self.current_id = start
        self.end_id = end
        self.lock = threading.Lock()

    def get_next_user_id(self):
        with self.lock:
            if self.current_id > self.end_id:
                raise ValueError("No more user IDs available.")
            user_id = self.current_id
            self.current_id += 1
            return user_id


# 全局列表，用于存储生成的token
tokens = []


# 线程工作函数
def thread_worker(generator):
    while True:
        try:
            # 获取下一个userId
            userId = generator.get_next_user_id()
            # 调用login函数
            token = login(userId)
            # 将token添加到全局列表
            tokens.append(json.dumps(token))
        except Exception as msg:
            print(msg)
            # 当没有更多userId时退出线程
            break


# 主函数
def main():
    # 创建UserIDGenerator实例
    user_id_generator = UserIDGenerator(800003400, 800003410)

    # 定义线程数量
    num_threads = 5
    threads = []

    # 创建并启动线程
    for i in range(num_threads):
        thread = threading.Thread(target=thread_worker, args=(user_id_generator,))
        thread.start()
        threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 所有线程完成后，将tokens列表中的token写入Redis列表
    # 假设你已经有一个名为redis_client的Redis客户端实例1
    print(f'共计：{len(tokens)}')
    TonUser().set_user(*tokens)


if __name__ == "__main__":
    main()
