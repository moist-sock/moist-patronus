import json


async def ctx_attachment_reader(ctx):
    return json.loads(await ctx.message.attachments[0].read())
