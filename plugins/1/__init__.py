from utils import Bot
from youtube_dl import YoutubeDL
from cogs.sakurabrand.plugin import PluginManager


class Music:
    
    def __init__(self, bot: Bot, manager: PluginManager):
        self.bot = bot
        self.manager = manager
        
    async def setdata(self, queue):
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True',
                       "ignoreerrors": True, "cookiefile": "data/youtube.com_cookies.txt"}
        if "twitch" in queue.url:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(queue.url, download=False)
            queue.source = info["formats"][0]['url']
            queue.title = info['title']
            queue.duration = info["duration"]
            queue.sid = "twitch:" + \
                info["webpage_url"].replace(
                    "https://m.twitch.tv/videos/", "")

    def restore(self, sid: str):
        return sid.replace("twitch:", "https://m.twitch.tv/videos/")
        
async def setup(bot: Bot, manager: PluginManager):
    await manager.add_class(music(bot, manager))
