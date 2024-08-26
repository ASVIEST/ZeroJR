from enum import Enum
from dataclasses import dataclass

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

@dataclass(frozen=True)
class Thread:
    auto_archive_duration : int
    invitable : bool
    locked : bool
    name : str
    slowmode_delay : int
    archived : bool
    type : ThreadType
    members_id : tuple[int]
    # history: 'History'

@dataclass(frozen=True)
class Message:
    display_name : str
    display_avatar_url : str
    content : str
    thread: Thread | None

@dataclass(frozen=True)
class History:
    messages : tuple[Message]

@dataclass(frozen=True)
class VoiceChannel:
    bitrate : int
    name : str
    slowmode_delay : int
    user_limit : int
    rtc_region : VoiceRegion
    type : VoiceType
    video_quality_mode : VideoQualityMode


#Без учёта прав доступа
@dataclass(frozen=True)
class TextChannel:
    default_auto_archive_duration : int
    default_thread_slowmode_delay : int
    name : str
    nsfw : bool
    slowmode_delay : int
    threads : tuple[Thread]
    topic : str

    history : History

@dataclass(frozen=True)
class Category:
    channels : tuple[TextChannel | VoiceChannel]
    name : str
    nsfw : bool
    position : int

@dataclass(frozen=True)
class Emoji:
    name : str
    data : bytes

@dataclass(frozen=True)
class Guild:
    name : str
    emojis : tuple[Emoji]
    categories : tuple[Category]
