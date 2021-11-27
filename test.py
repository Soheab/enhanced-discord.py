from discord.ext import commands
from discord import Intents, Member, User, guild

bot = commands.Bot(command_prefix="...", intents=Intents.all())


async def send(ctx, *text):
    await ctx.send("\n".join(f"{str(x)=}" for x in text))


@bot.command()
async def lol(ctx, m: Member):
    await ctx.send(str((await ctx.guild.fetch_member(m.id)).banner))


@bot.command()
async def banner(ctx, m: Member):
    upgraded = await m.upgrade(banner=True)
    await ctx.send(f"{type(m)=}\n{m.banner=}\n{type(upgraded)}\n{upgraded.banner=}")


@bot.command()
async def tomember(ctx, m: User):
    upgraded = await m.upgrade(guild=ctx.guild)
    await ctx.send(f"{type(m)=}\n{type(upgraded)=}")


@bot.command()
async def memberandbanner(ctx, m: User):
    upgraded = await m.upgrade(guild=ctx.guild, banner=True)
    await ctx.send(f"{type(m)=}\n{type(upgraded)=}\n{m.banner=}\n{upgraded.banner=}")


bot.run("haha yes")
