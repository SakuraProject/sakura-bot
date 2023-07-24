import discord
from discord.ext import commands

from diffusers import DiffusionPipeline
import torch


class Imagine(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.pipe = DiffusionPipeline.from_pretrained("hakurei/waifu-diffusion", torch_dtype=torch.float16)
        self.pipe.to("cuda")
