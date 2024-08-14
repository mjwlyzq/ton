import json
import random
import time
import uuid
from time import sleep

from libs.eventReport import EventReport
from libs.logger import log
from libs.public import LocustPublic
from libs.timeUtil import TimeUtil


class TonClient(object):
    def __init__(self):
        super(TonClient, self).__init__()
        self.actionIndex = 0  # 用户未选择行动
        self.chapterNum = None  # 已经在挑战的步骤
        self.actionStartStatus = False  # 是否已经存在挑战
        self.successful = False  # 挑战是否成功
        self.actionStatus = False  # 挑战是否完成
        self.challengeId = None
        self.taskId = None
        self.totalChapter = 0  # 总共创建了几章节
        self.running = True
        self.round = None
        self.tokenType = None
        self.landIndex = None
        self.startTimestamp = None
        self.ton_headers = None
        self.userinfo = None
        self.httpClient = None
        self.base_url = 'https://apiv2.gabby.world/api/ton'
        self.adventureList = []  # 已经存在玩家的地块列表
        self.blockUser = 9999  # 0表示允许创建新的章节
        self.adventureId = None  # 玩家id
        self.needTotalChapter = 3  # 需要创建章节的数量

    def prepare(self, client, userinfo, value):
        self.httpClient = client
        self.userinfo = userinfo
        self.ton_headers = LocustPublic.ton_headers(self.userinfo)
        # location = self.userinfo.get('location')
        self.adventureId = value
        log.info(f'获取到token：{self.ton_headers}')
        self.startTimestamp = TimeUtil.now()

    def send_post(self, client, userinfo, value):
        self.prepare(client, userinfo, value)
        self.create_gabby()  # 创建gabby
        self.user_info()  # 校验用户信息
        self.map_location_info()  # 查看地图坐标信息
        self.adventure_info(self.adventureId)  # 创建完成的adventureId
        if not self.adventureList:
            log.info(f'地图中没有找到可用的地块')
            return
        # while True:
        #     self.adventure_info(self.adventureId)
        #     if self.totalChapter >= self.needTotalChapter:
        #         log.info(f'获取到章节数量：{self.totalChapter} >= 3，进入挑战环节')
        #         self.running = True  # 开启挑战
        #         break
        #     if self.blockUser == 0:
        #         self.task_block()  # 创建chapter
        #         log.info(f'创建第 {self.totalChapter + 1} 章')
        #     log.info(f'等待20秒后检查第{self.totalChapter + 1}章节是否创建成功')
        #     sleep(20)
        last_running_timestamp = TimeUtil.now()
        while self.running:
            try:
                if TimeUtil.now() - last_running_timestamp > 60 * 1000:
                    EventReport.success(name="循环超时", response_time=TimeUtil.now() - last_running_timestamp)
                last_running_timestamp = TimeUtil.now()
                self.challenge_info()  # 查看用户上次挑战信息
                if not self.actionStartStatus:  # 如果用户没有挑战过
                    log.info(f'用户首次参加挑战')
                    self.challenge_start(1, 0)
                    self.challenge_action(1, self.challengeId)  # 选择行动
                    self.action_dice(1, self.challengeId)  # 丢色子
                else:
                    self.challenge_detail(self.chapterNum, self.challengeId)
                    if self.actionStatus:
                        if self.successful:
                            log.info('用户上个挑战完成且挑战成功')
                            if self.chapterNum + 1 < self.totalChapter:
                                self.challenge_start(self.chapterNum + 1, self.challengeId)  # 如果挑战成功，开启新的章节挑战
                                self.challenge_action(self.chapterNum + 1, self.challengeId)  # 选择行动
                                self.action_dice(self.chapterNum + 1, self.challengeId)  # 丢色子
                            else:
                                self.challenge_close(self.challengeId)
                                log.info(f"完成挑战，所有挑战结束")
                                break
                        else:
                            log.info('用户上个挑战已完成，但挑战失败')
                            self.challenge_start(1, 0)
                            self.challenge_action(1, self.challengeId)  # 选择行动
                            self.action_dice(1, self.challengeId)  # 丢色子
                    else:
                        log.info(f'上个章节挑战还未出结果，开始选择挑战&丢色子')
                        if self.actionIndex == 0:  # 如果用户未选择行动
                            self.challenge_action(self.chapterNum, self.challengeId)  # 选择行动
                        self.action_dice(self.chapterNum, self.challengeId)  # 丢色子
                now = TimeUtil.now()
                cost = now - last_running_timestamp
                if cost < 500:
                    time.sleep((500 - cost) / 1000)
            except Exception as err:
                pass
            finally:
                now = TimeUtil.now()
                cost = now - last_running_timestamp
                if cost < 1000:
                    time.sleep((1000 - cost) / 1000)

    def create_gabby(self):
        desc = '(创建gabby)'
        payload = {
            "name": f"性能测试={uuid.uuid4().hex[:8]}",
            "attr": {
                "hp": 1,
                "def": 1,
                "dmg": 1,
                "str": 1,
                "dex": 1,
                "int": 1,
                "cha": 1
            },
            "code": ""
        }
        url = f'{self.base_url}/user/createGabby'
        LocustPublic.post_ignore(self.httpClient, url, self.ton_headers, payload, desc)

    def user_info(self):
        desc = '(用户信息)'
        payload = {}
        url = f'{self.base_url}/user/info'
        LocustPublic.get(self.httpClient, url, self.ton_headers, payload, desc)

    def map_location_info(self):
        desc = '(地图坐标信息)'
        payload = {}
        url = f'{self.base_url}/land/map/1'
        result = LocustPublic.get(self.httpClient, url, self.ton_headers, payload, desc)
        data = result.get('data')
        # 找到已经存在玩家的地块列表
        # 那就是两种了，一种userId !=0 and adventureId == 0  or adventureId != 0
        # self.adventureList = list(filter(lambda ad: ad.get("adventureId", 0) > 0 or ad.get('userId', 0) == 0
        #                                             and ad.get("adventureId", 0) == 0, data))
        self.adventureList = list(filter(lambda ad: ad.get("adventureId", 0) > 0 and ad.get('landIndex', 0)
                                                    not in [i for i in range(1, 11)], data))
        if self.adventureList:
            # self.adventureId = random.choice(self.adventureList).get('adventureId')
            # self.adventureId = 325
            pass

    def adventure_info(self, adventureId):
        desc = '(创建完成的adventure信息)'
        payload = {}
        url = f'{self.base_url}/adventure/{adventureId}'
        result = LocustPublic.get_ignore(self.httpClient, url, self.ton_headers, payload, desc)
        data = result.get('data')
        if data is not None:
            # 获取是否允许在地块创建新的章节，0表示可以创建
            self.blockUser = data.get('blockUser')
            self.landIndex = data.get('landIndex')
            self.tokenType = data.get('tokenType')
            self.round = data.get('round')
            self.totalChapter = data.get('totalChapter')

    def task_block(self):
        desc = '(创建chapter)'
        payload = {
            "adventureId": self.adventureId,  # 当前地块不存在adventure得时候填0
            "tokenType": self.tokenType,  # gp或者ton局 tokenType的值: 1=>gp 2=>ton 3=>prompt
            "location": 1,  # 写死1
            "landIndex": self.landIndex,  # 地块的坐标 1.10 接⼝获取
            "chapterNum": self.totalChapter + 1,  # 需要创建的章节
            "round": self.round  # 1.10 接⼝获取, adventureId为0的时候传递
        }
        log.info(f'创建chapter：{json.dumps(payload)} headers：{self.ton_headers}')
        url = f'{self.base_url}/adventure/task/block'
        result = LocustPublic.post_ignore(self.httpClient, url, self.ton_headers, payload, desc)
        data = result.get('data')
        if data is not None:
            self.taskId = data.get('taskId')
            self.task_submit()  # 提交创建的任务

    def task_submit(self):
        desc = '(提交创建任务的prompt)'
        payload = {

            "taskId": self.taskId,  # block 接⼝返回的taskId
            "chapterParams": {
                "scenarios": ["dsdasd"],
                "challenges": ["dsdadas"],
                "challengeMode": 1
            },
            "npcId": 0,  # ⽤⼾选择已有的npc才填
            "npc": {  # ⽣成新的npc
                "prompt": ["dasdasdas"],
                "attr": {
                    "hp": 5,
                    "def": 1,
                    "dmg": 1,
                    "str": 2,
                    "dex": 1,
                    "int": 3,
                    "cha": 2
                }

            }
        }
        url = f'{self.base_url}/adventure/task/submit'
        LocustPublic.post_ignore(self.httpClient, url, self.ton_headers, payload, desc)

    def challenge_info(self):
        desc = '(获取⽤⼾挑战信息)'
        payload = {}
        url = f'{self.base_url}/challenge/last'
        result = LocustPublic.get_ignore(self.httpClient, url, self.ton_headers, payload, desc)
        data = result.get('data')
        if data is not None:
            user_id = data.get('userId')
            if user_id != 0:
                self.actionStartStatus = True
                self.challengeId = data.get('id')
                self.chapterNum = data.get('chapterNum')

    def challenge_start(self, chapterNum, challengeId):
        desc = '(开启新章节的挑战)'
        payload = {
            "adventureId": self.adventureId,
            "chapterNum": chapterNum,
            "challengeId": challengeId  # 选填（挑战第⼀章的时候不需要， 其他情况必须带）
        }
        url = f'{self.base_url}/challenge'
        result = LocustPublic.post(self.httpClient, url, self.ton_headers, payload, desc)
        data = result.get('data')
        self.challengeId = data.get('challengeId')

    def challenge_detail(self, chapterNum, challengeId):
        desc = '(获取挑战详情)'
        payload = {
            "challengeId": challengeId,
            "chapterNum": chapterNum,
        }
        url = f'{self.base_url}/challenge/detail'
        result = LocustPublic.get_ignore(self.httpClient, url, self.ton_headers, payload, desc)
        data = result.get('data')
        if data:
            self.actionStatus = data.get('done')
            self.successful = data.get('successful')
            self.actionIndex = data.get('actionIndex')

    def challenge_action(self, chapterNum, challengeId):
        desc = '(选择挑战行动)'
        payload = {
            "challengeId": challengeId,
            "chapterNum": chapterNum,
            "action": 1
        }
        url = f'{self.base_url}/challenge/action'
        LocustPublic.post(self.httpClient, url, self.ton_headers, payload, desc)

    def action_dice(self, chapterNum, challengeId):
        desc = '(丢骰⼦出结果)'
        payload = {
            "challengeId": challengeId,
            "chapterNum": chapterNum
        }
        url = f'{self.base_url}/challenge/action/dice'
        LocustPublic.post(self.httpClient, url, self.ton_headers, payload, desc)

    def challenge_close(self, challengeId):
        desc = '(结束挑战任务)'
        payload = {
            "challengeId": challengeId
        }
        url = f'{self.base_url}/challenge/close'
        LocustPublic.post(self.httpClient, url, self.ton_headers, payload, desc)
