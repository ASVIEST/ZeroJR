from rich import inspect
import discord
from enum import Enum

import requests

class ThreadType(Enum):
    news_thread = 10
    public_thread = 11
    private_thread = 12


class VoiceType(Enum):
    voice = 2
    stage_voice = 13


class VideoQualityMode(Enum):
    auto = 1
    full = 2


class VoiceRegion(Enum):
    us_west = "us-west"
    us_east = "us-east"
    us_south = "us-south"
    us_central = "us-central"
    eu_west = "eu-west"
    eu_central = "eu-central"
    singapore = "singapore"
    london = "london"
    sydney = "sydney"
    amsterdam = "amsterdam"
    frankfurt = "frankfurt"
    brazil = "brazil"
    hongkong = "hongkong"
    russia = "russia"
    japan = "japan"
    southafrica = "southafrica"
    south_korea = "south-korea"
    india = "india"
    europe = "europe"
    dubai = "dubai"
    vip_us_east = "vip-us-east"
    vip_us_west = "vip-us-west"
    vip_amsterdam = "vip-amsterdam"

    default = "default"


class Message():
    display_name : str
    display_avatar_url : str
    content : str

    def __init__(self, message: discord.Message):
        self.display_name = message.author.display_name
        self.display_avatar_url = message.author.display_avatar.url
        self.content = message.content


class History():
    messages : list[Message]

    def __init__(self):
        self.messages = []
    
    def join_messages(self):
        print("Начали слипаться")

        #Проверка на пустой канал (или канал с одним сообщением)
        if len(self.messages) <= 1:
            return
        messages_sliplis = [self.messages[0]]
        for message in self.messages[1:]:
            #А потом у двух товарищей совпадёт аватарка...
            if message.display_avatar_url == messages_sliplis[-1].display_avatar_url and len(messages_sliplis[-1].content + "\n" + message.content) <= 2000:
                messages_sliplis[-1].content += "\n" + message.content
                print("Сообщения слиплись!")
            else:
                messages_sliplis.append(message)
                print("Сообщения не слиплись!")
        self.messages = messages_sliplis
        print("Слипиши!")

    async def avisitor(self, history):
        print("History avisitor()")
        async for message in history:
            if message.content != "":
                self.messages.append(Message(message))
                print(f"Добавлено сообщение: {message.content}")
        self.messages.reverse()
        self.join_messages()


class Thread():
    auto_archive_duration : int
    invitable : bool
    locked : bool
    name : str
    slowmode_delay : int
    archived : bool
    type : ThreadType
    members_id : list[int]

    def __init__(self, thread: discord.Thread):
        self.invitable = thread.invitable
        self.locked = thread.locked
        self.name = thread.name
        self.slowmode_delay = thread.slowmode_delay
        self.archived = thread.archived
        self.auto_archive_duration = thread.auto_archive_duration
        self.type = ThreadType(thread.type.value)
        self.members_id = []

    #см. avisitor ниже
    async def avisitor(self, thread : discord.Thread):
        print("Thread avisitor()")
        await thread.fetch_members()
        for i in thread.members:
            self.members_id.append(i.id)

    def as_dict(self):
        return {"invitable": self.invitable,
         "locked": self.locked,
         "name": self.name,
         "slowmode_delay": self.slowmode_delay,
         "auto_archive_duration": self.auto_archive_duration,
         "archived": self.archived}


class VoiceChannel():
    bitrate : int
    name : str
    slowmode_delay : int
    user_limit : int
    rtc_region : VoiceRegion
    type : VoiceType
    video_quality_mode : VideoQualityMode

    def __init__(self, channel: discord.VoiceChannel):
        self.bitrate = channel.bitrate
        self.name = channel.name
        self.slowmode_delay = channel.slowmode_delay
        self.user_limit = channel.user_limit
        if channel.rtc_region != None:
            self.rtc_region = VoiceRegion(channel.rtc_region.value)
        else:
            self.rtc_region = VoiceRegion.default
        self.type = VoiceType(channel.type.value)
        self.video_quality_mode = VideoQualityMode(channel.video_quality_mode.value)

    #Для чего я создан?
    #Стать заглушкой.
    #Боже мой...
    async def avisitor(self, channel: discord.VoiceChannel):
        print("VoiceChannel avisitor()")
        pass

    def as_dict(self):
        d = {"bitrate": self.bitrate,
                "name": self.name,
                "slowmode_delay": self.slowmode_delay,
                "user_limit": self.user_limit,
                "video_quality_mode": discord.VideoQualityMode(self.video_quality_mode.value)}
        
        #При инциализации нашего класса VoiceChannel channel.rtc_region может быть равен None, но т.к. нам обязательно нужно инициализировать поле, мы указываем своё значение
        #default в Enum'e. А здесь проверяем, нужно ли нам возвращать rtc_region или оставить его пустым (если во время инициализации он шизанулся в default)
        if self.rtc_region != VoiceRegion.default:
            d["rtc_region"] = discord.VoiceRegion(self.rtc_region.value)
        return d


#Без учёта прав доступа
class TextChannel():
    default_auto_archive_duration : int
    default_thread_slowmode_delay : int
    name : str
    nsfw : bool
    slowmode_delay : int
    threads : list[Thread]
    topic : str

    history : History

    def __init__(self, channel: discord.TextChannel):
        self.default_auto_archive_duration = channel.default_auto_archive_duration
        self.default_thread_slowmode_delay = channel.default_thread_slowmode_delay
        self.name = channel.name
        self.nsfw = channel.nsfw
        self.slowmode_delay = channel.slowmode_delay
        self.topic = channel.topic
        self.threads = []
        for i in channel.threads:
            thrd = Thread(i)
            self.threads.append(thrd)

        self.history = History()
    
    #см. avisitor ниже
    async def avisitor(self, channel: discord.TextChannel):
        print("TextChannel avisitor()")
        for record_thread, thread in zip(self.threads, channel.threads):
                await record_thread.avisitor(thread)

        await self.history.avisitor(channel.history(limit = None))

    def as_dict(self):
        return {"default_auto_archive_duration": self.default_auto_archive_duration,
                "default_thread_slowmode_delay": self.default_thread_slowmode_delay,
                "nsfw": self.nsfw,
                "slowmode_delay": self.slowmode_delay,
                "topic": self.topic}


class Category():
    channels : list[TextChannel | VoiceChannel]
    name : str
    nsfw : bool
    position : int
    CHANNEL_CONVERTER = {discord.TextChannel: TextChannel,
                         discord.VoiceChannel: VoiceChannel}

    def __init__(self, category: discord.CategoryChannel):
        self.name = category.name
        self.nsfw = category.nsfw
        self.position = category.position
        self.channels = []
        for i in category.channels:
            chan = self.CHANNEL_CONVERTER[type(i)](i)
            inspect(chan)
            print("record.Category (CHANNEL_CONVERTER закончил шизить).")
            self.channels.append(chan)
    
    #Итак, ты не понимаешь, в чём смысл этого асинхронного говна? Оно работает, двигая бесполезный кусок переменной вниз по дереву, вызывая avisitor до Thread.
    #Это нужно для того, чтобы заполнить массив thread.members, вызвав thread.fetch_members(), которому нужен ебучий await. Зато теперь у нас есть возможность вызывать любую
    #асинхронную шизу на любом моменте выполенния... Ура... Да...
    async def avisitor(self, category: discord.CategoryChannel):
        print("Category avisitor()")
        for record_channel, channel in zip(self.channels, category.channels):
                await record_channel.avisitor(channel)

    def as_dict(self):
        return {"nsfw": self.nsfw}


class Emoji():
    name : str
    data : bytes

    def __init__(self, _name, _data):
        self.name = _name
        self.data = _data


class Guild():
    name : str
    emojis : list[Emoji]
    categories : list[Category]

    def __init__(self, guild: discord.Guild):
        self.name = guild.name
        self.emojis = []
        for emoji in guild.emojis:
            self.emojis.append(Emoji(emoji.name, requests.get(emoji.url).content))
        self.categories = []
        
    async def avisitor(self, guild : discord.Guild):
        print("Guild avisitor()")
        for category in guild.categories:
            category_obj = Category(category)
            await category_obj.avisitor(category)
            self.categories.append(category_obj)
    
    def as_dict(self):
        return {"name": self.name}