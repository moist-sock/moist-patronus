from discord.ext import commands
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


async def send_email(notification):
    current_time = datetime.now().strftime('%H:%M:%S')
    SMTP_SERVER = "smtp.mail.yahoo.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "lhraider2@yahoo.com"
    SMTP_PASSWORD = "bsjfsjarmtrirqjr"
    EMAIL_FROM = "lhraider2@yahoo.com"
    EMAIL_TO = "moists0ck0001@gmail.com"
    EMAIL_SUBJECT = notification
    co_msg = current_time
    msg = MIMEText(co_msg)
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mail.starttls()
    mail.login(SMTP_USERNAME, SMTP_PASSWORD)
    mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    mail.quit()


class Vyre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != 1224440634161500221:
            return

        messages_to_check_for = ["<@965663111996669992> Random event spawned: Genie",
                                 "<@965663111996669992> NPC aggression has expired!",
                                 "<@965663111996669992> You received a highlighted drop: Unidentified large fossil",
                                 "<@965663111996669992> You received a highlighted drop: Unidentified medium fossil",
                                 "<@965663111996669992> You received a highlighted drop: Unidentified rare fossil",
                                 "<@965663111996669992> You received a highlighted drop: Shield left half",
                                 "<@965663111996669992> You received a valuable drop: Blood shard"
                                 ]
        if message.content not in messages_to_check_for:
            return
        notification = message.content.split('>', 1)[1].strip()

        if "You received a highlighted drop:" in notification: 
            notification = notification[33:] + " !!!"

        return await send_email(notification)

    async def msg_moist(self):
        await self.bot.get_user(self.bot.settings.moist_id).send(
            "You need to reset crab aggro king")


async def setup(bot):
    await bot.add_cog(Vyre(bot))
