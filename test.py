from discord.ext import commands

from discord import Intents, File, interactions
import discord
from discord.mentions import AllowedMentions


bot = commands.Bot("...?", intents=Intents.all(), slash_commands=True, slash_command_guilds=[890673374731321395])
bot.load_extension("jishaku")


@bot.command()
async def test(ctx):
    print(ctx.message.attachments)
    file = File("C:/Users/Sohea/OneDrive/Afbeeldingen/That_goes_in_here.jpg")
    print(file)
    msg = await ctx.send(
        "yes <@150665783268212746>",
        file=file,
        return_message=False,
        embed=discord.Embed(title="test", description="test"),
    )
    # print(msg, msg.edit, type(msg))


#  await ctx.interaction.edit_original_message(content="test")


@bot.command()
async def button(ctx):
    async def callback(inter):
        print("called")
        file = File("C:/Users/Sohea/OneDrive/Afbeeldingen/That_goes_in_here.jpg")

        await inter.response.send_message(
            content="hello",
            files=[file],
            #  delete_after=5,
            # ephemeral=True,
        )

    yes = discord.ui.View()
    bv = discord.ui.Button(label="Yes")
    bv.callback = callback
    yes.add_item(bv)
    print(ctx.send, type(ctx.send))
    await ctx.send(
        "yes <@150665783268212746>",
        view=yes,
        allowed_mentions=AllowedMentions(users=True, replied_user=True),
    )


bot.run("ODkwNjczNzkwNTg4MTcwMjQx.YUzOmw.7WR7VBZjACb7JFloeF1XtYpkFgI")
