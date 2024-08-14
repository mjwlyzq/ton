import json

import requests

from myRedis import getRedisSession, RedisDbIndexEnum


class TonUser:
    def __init__(self):
        self.rb = getRedisSession(redisDbIndex=RedisDbIndexEnum.ton)
        self.name = 'locust'
        self.runUser = 'runUser'
        self.adventureId = 'adventureId'
        self.ton_headers = {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjk5OTk5OTkxMCwibmFtZSI6IiIsImFkZHJlc3MiOiIiLCJleHAiOjE3MzEzMzYxNzYsIm5iZiI6MTcyMjY5NjE3Nn0.n55TDWY57QVbElFbTHvzcBG46sO7imG5WEOD8jYaTH0"
        }

    def get_one_user(self):
        s = self.rb.rpop(self.runUser)
        return s

    def set_user(self, *values):
        # self.delete_user(self.name)
        self.rb.lpush(self.name, *values)

    def get_value(self):
        # self.delete_user(self.name)
        return self.rb.get(self.adventureId)

    def get_user(self):
        return self.rb.lrange(self.name, 0, -1)

    def delete_user(self, key):
        self.rb.delete(key)

    def init_user(self):
        self.delete_user(self.runUser)
        u = self.get_user()
        print(len(u))
        self.rb.rpush(self.runUser, *u)

    def map_location_info(self):
        url = 'https://apiv2.gabby.world/api/ton/land/map/1'
        result = requests.get(url, headers=self.ton_headers).json()
        data = result.get('data')
        # 找到已经存在玩家的地块列表
        adventure_list = list(
            filter(lambda ad: ad.get("adventureId") > 0 and ad.get('landIndex', 0)
                              not in [i for i in range(1, 11)] or (ad.get('userId') == 0 and ad.get("adventureId") == 0
                                                                   and ad.get('landIndex', 0) not in [i for i in range(1, 11)]),
                   data))
        print([i.get("adventureId") for i in adventure_list])
        print(len(adventure_list))
        return adventure_list

    def init_user_2(self):
        self.delete_user(self.runUser)
        location_info = self.map_location_info()
        u = self.get_user()[:len(location_info)]
        # 确保用户数据和地图坐标数据的数量相同
        if len(u) != len(location_info):
            raise ValueError("The number of user data and location data must be the same.")

        # 创建用户数据与地图坐标信息对应的字典列表
        user_location_list = []
        for user_token, location_data in zip(u, location_info):
            user_location_dict = {
                "token": json.loads(user_token),
                "location": location_data
            }
            user_location_list.append(json.dumps(user_location_dict))
        # 将JSON字符串列表推入到Redis列表中
        self.rb.rpush(self.runUser, *user_location_list)


if __name__ == "__main__":
    t = TonUser()
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjk5OTk5OTkxMiwibmFtZSI6IiIsImFkZHJlc3MiOiIiLCJleHAiOjE3MzE0MjAwMDIsIm5iZiI6MTcyMjc4MDAwMn0.t00sk6mEUoyt8aJWr4VoJBkCEuhDi3c5NZqhnhu9vv0'
    # t.set_user(token)
    t.init_user()
