import json

import redis
from enum import Enum


# from conf.config import REDIS
#
# class MyRedis(object):
#     def __init__(self, host=REDIS.get('ip'), port=REDIS.get('port'), password=REDIS.get('password'),
#                  db=REDIS.get('db').get('smooth')):
#         pool = redis.ConnectionPool(host=host, port=port, password=password,
#                                     decode_responses=True, db=db)
#         self.r = redis.Redis(connection_pool=pool)
#
#     @property
#     def db(self):
#         return self.r
#
#     def rm_smooth(self, interactId):
#         self.r.delete(f'SMOOTH:LiveAnswerDetail_interactId:{interactId}')


class RedisDbIndexEnum(Enum):
    smooth = 35
    local = 15
    env = 'together'
    ton = 0


_smooth_redis_connect_pool = redis.ConnectionPool(host='',
                                                  password='',
                                                  port=6379,
                                                  db=RedisDbIndexEnum.smooth.value,
                                                  max_connections=5)

_local_redis_connect_pool = redis.ConnectionPool(host='',
                                                 port=6379,
                                                 db=RedisDbIndexEnum.local.value,
                                                 max_connections=100000)

_ton_redis_connect_pool = redis.ConnectionPool(host='3.112.1.126',
                                               port=6379,
                                               db=RedisDbIndexEnum.ton.value,
                                               max_connections=100000)

_smooth_redis = redis.Redis(connection_pool=_smooth_redis_connect_pool, decode_responses=True)
_local_redis = redis.Redis(connection_pool=_local_redis_connect_pool, decode_responses=True)
_ton_redis = redis.Redis(connection_pool=_ton_redis_connect_pool, decode_responses=True)


def getRedisSession(redisDbIndex: RedisDbIndexEnum = RedisDbIndexEnum.local):
    if redisDbIndex == RedisDbIndexEnum.smooth:
        return _smooth_redis
    elif redisDbIndex == RedisDbIndexEnum.local:
        return _local_redis
    elif redisDbIndex == RedisDbIndexEnum.ton:
        return _ton_redis


def push_locust(key, value):
    """
    :return:
    """
    _local_redis.rpush(f'locust:{RedisDbIndexEnum.env}:{key}', json.dumps(value))


def rm_locust(key):
    """
    :return:
    """
    _local_redis.delete(f'locust:{RedisDbIndexEnum.env}:{key}')


def get_range(key):
    """
    :return:
    """
    getInfo = _local_redis.lrange(f'locust:{RedisDbIndexEnum.env}:{key}', 0, -1)
    return [json.loads(i) for i in getInfo]


def get_range_count(key):
    """
    :return:
    """
    getInfo = _local_redis.lrange(f'locust:{RedisDbIndexEnum.env}:{key}', 0, -1)
    return len(getInfo)


def get_range_pop(key):
    """
    :return:
    """
    getInfo = _local_redis.lpop(f'locust:{RedisDbIndexEnum.env}:{key}')
    try:
        getInfo = json.loads(getInfo)
    except Exception as msg:
        getInfo = None
    return getInfo


if __name__ == '__main__':
    # deleteKey = ['joinRoom', 'enterRoom', 'createRoomUser', 'roomUser', 'roomIdList']
    # for i in deleteKey:
    #     rm_locust(i)
    # rm_locust('aaa')
    # push_locust('aaa', {'name': 'abc'})
    # a = get_range('aaa')
    # print(a)
    # b = get_range_count('aaa')
    # print(b)
    # c = get_range_count('createRoomUser')
    # print(c)
    # c = get_range_count('joinRoom')
    # print(c)
    from tools.create_room import Enm

    a = get_range(Enm.UserInfo)
