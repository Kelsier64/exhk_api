import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from dotenv import load_dotenv
import os
from img_processor import ExamProcessor
from datetime import datetime
import asyncio
from gtts import gTTS
import time

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

if token is None:
    raise ValueError("DISCORD_BOT_TOKEN1 環境變數未設置")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

processor = ExamProcessor()

@bot.event
async def on_ready():
    await bot.tree.sync()  # 同步指令
    command_count = len(bot.tree.get_commands())
    
    print(f"Bot is ready. 名稱 ---> {bot.user}")
    print(f"已載入 {command_count} 項指令")

@bot.event
async def on_disconnect():
    print("Bot is disconnected")

async def speak_text(text: str):
    if not bot.voice_clients:
        print("Bot 不在任何語音頻道中")
        return
    
    vc = bot.voice_clients[0]
    while vc.is_playing():
        await asyncio.sleep(0.1) 

    tts = gTTS(text, lang='zh')
    filename = "speech.mp3"
    tts.save(filename)

    vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: print(f"播放完成: {e}"))

@bot.tree.command(name="ping", description="查看延遲")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"延遲: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="upload", description="上傳文件")
async def upload(interaction: discord.Interaction, file: discord.Attachment):
    if file.filename.split('.')[-1].lower() not in {'png', 'jpg', 'jpeg', 'gif'}:
        await interaction.response.send_message("文件類型不允許")
        return

    await interaction.response.send_message("文件正在處理，請稍候...")

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"{timestamp}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join('imgs', new_filename)
    
    await file.save(file_path)
    
    for ans in processor.main("math/image1.png"):
        print("generated:"+ans)
        await speak_text(ans)

    await interaction.followup.send(f"文件處理完成: {new_filename}")


@bot.tree.command(name="reload", description="重新加載處理器")
async def reload_processor(interaction: discord.Interaction):
    global processor
    processor = ExamProcessor()
    await interaction.response.send_message("處理器已重新加載")

@bot.tree.command(name="join", description="加入語音頻道")
async def join(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message("你不在語音頻道中")
        return

    channel = interaction.user.voice.channel
    if bot.voice_clients:
        await bot.voice_clients[0].move_to(channel)
    else:
        await channel.connect()
    await interaction.response.send_message(f"已加入語音頻道: {channel.name}")

@bot.tree.command(name="leave", description="離開語音頻道")
async def leave(interaction: discord.Interaction):
    if not bot.voice_clients:
        await interaction.response.send_message("Bot 不在任何語音頻道中")
        return

    await bot.voice_clients[0].disconnect()
    await interaction.response.send_message("已離開語音頻道")



if __name__ == "__main__":
    bot.run(token)