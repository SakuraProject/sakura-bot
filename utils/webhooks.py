# Sakura utils - webhooks

import discord


async def get_webhook(channel: discord.TextChannel, count: int = 0) -> discord.Webhook:
    """Webhookを検索します。"""
    webhooks = await channel.webhooks()
    webhook = discord.utils.get(webhooks, name=f"sakura-tools{count}")
    if webhook is None:
        webhook = await channel.create_webhook(name=f"sakura-tools{count}")
    if not (webhook.type == discord.WebhookType.incoming and webhook.token is not None):
        return await get_webhook(channel, count + 1)
    return webhook
