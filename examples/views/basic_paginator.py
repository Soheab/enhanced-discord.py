from typing import Optional, Dict, Any, List, Union, Tuple

import discord
from discord.ext import commands


class PaginatorButton(discord.ui.Button["Paginator"]):
    def __init__(self, *, label: str, style: discord.ButtonStyle = discord.ButtonStyle.blurple):
        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None  # so that the type checker doesn't complain

        # Set the current_page attribute to th correct page

        if self.custom_id == "right_button":
            self.view.current_page += 1
        elif self.custom_id == "left_button":
            self.view.current_page -= 1

        # Update the paginator

        # easier to access
        left_button: PaginatorButton = discord.utils.get(self.view.children, custom_id="left_button")  # type: ignore
        right_button: PaginatorButton = discord.utils.get(self.view.children, custom_id="right_button")  # type: ignore

        # disable the buttons if needed

        if self.view.current_page >= self.view.max_pages - 1:
            right_button.disabled = True
        elif self.view.current_page <= 0:
            left_button.disabled = True
        else:
            right_button.disabled = False
            left_button.disabled = False

        keywords, _ = self.view.handle_page_content()
        assert interaction.message is not None
        await interaction.message.edit(**keywords)


class Paginator(discord.ui.View):
    def __init__(
        self,
        pages: Union[List[discord.Embed], List[str]],
        *,
        author_id: int = None,
        disable_on_timeout: bool = False,
        timeout: int = 180,
    ):

        # dict of default buttons
        DEFAULT_BUTTONS: Dict[str, PaginatorButton] = {
            "left": PaginatorButton(label="Left", style=discord.ButtonStyle.primary),
            "right": PaginatorButton(label="Right", style=discord.ButtonStyle.primary),
        }

        super().__init__(timeout=timeout)

        # assign the basic attributes

        self._author_id = author_id
        self._disable_on_timeout = disable_on_timeout
        self.buttons: Dict[str, PaginatorButton] = DEFAULT_BUTTONS

        self.message: Optional[discord.Message] = None

        # for the pages
        self.pages: Union[List[discord.Embed], List[str]] = pages
        self.current_page: int = 0
        self.max_pages = len(self.pages)
        self.page_string = f"Page {self.current_page}/{self.max_pages}"

        # adds the buttons to the view
        self.add_buttons()

    def add_buttons(self):
        if all(b in ["left", "right"] for b in self.buttons.keys()) is False:
            raise ValueError("Paginator buttons must have a left and right button")

        button: PaginatorButton

        # loop through the buttons and adding them to the view
        for name, button in self.buttons.items():
            if not isinstance(button, PaginatorButton):
                raise TypeError(f"{button.__class__} is not a PaginatorButton")

            # set the custom_id
            button.custom_id = f"{name}_button"

            # check if the button label is called left or right
            if button.custom_id == "left_button":
                # disable the button if the current page is or is below 0 aka there no page to go back to
                if self.current_page <= 0:
                    button.disabled = True
            else:
                button.disabled = False

            if button.custom_id == "right_button":

                # disable the button if the current page is or is above the max pages aka there no page to go to
                if self.current_page >= self.max_pages - 1:
                    button.disabled = True
            else:
                button.disabled = False
            self.add_item(button)

    # main way to send the menu
    async def send(
        self, send_to: Union[discord.abc.Messageable, discord.Message], *args: Any, **kwargs: Any
    ) -> discord.Message:

        # get the page content
        keywords, kwargs = self.handle_page_content(kwargs)  # type: ignore

        # raise if send_to is None
        if not send_to:
            raise ValueError("send_to can not be None")

        # check if send_to is a message or channel. If it is a message we reply to it else we send it to the channel
        if isinstance(send_to, discord.Message):
            # send_to is a message, so we reply to it
            self.message = await send_to.reply(*args, **keywords, **kwargs)  # type: ignore
        else:
            # send_to is a channel, so we send it
            self.message = await send_to.send(*args, **keywords, **kwargs)  # type: ignore

        # return the sent message
        assert self.message is not None  # so that the type checker doesn't complain
        return self.message

    def handle_page_content(
        self, kwargs: Optional[Any] = None
    ) -> Union[Tuple[Dict[str, Any], None], Tuple[Dict[str, Any], Dict[str, Any]], Tuple[dict, None]]:
        self.page_string: str = f"Page {self.current_page + 1}/{self.max_pages}"  # type: ignore

        # get page content aka see if it's an embed or string.
        keywords = self.get_page_data(self.current_page)

        # check if keywords is None aka page is over the max pages
        if keywords is None:
            return {}, kwargs

        if kwargs is not None:
            # remove any content and embeds provided via send because that will conflict with the page content
            try:
                del kwargs["content"]
                del kwargs["embed"]
                del kwargs["embeds"]
            except KeyError:
                pass

        # check if page is a string
        if keywords["content"] is not None:
            # add the page string (current_page/max_pages) as content after the page content
            keywords["content"] += f"\n\n{self.page_string}"

        # check if page is an embed
        elif keywords["embed"] is not None:
            # add the page string (current_page/max_pages) as the footer of the embed
            keywords["embed"].set_footer(text=self.page_string)

        return keywords, kwargs

    def get_page_data(self, page_number: int) -> Optional[Dict[str, Any]]:
        page: Union[str, discord.Embed, None]

        # check if page is over the max pages and return None
        if page_number < 0 or page_number >= self.max_pages:
            return None
        else:
            # get the page
            page = self.pages[page_number]

            # check if page is a string
            if isinstance(page, str):
                return {"content": page, "embed": None, "view": self}

            # check if the page is an embed
            elif isinstance(page, discord.Embed):
                return {"content": None, "embed": page, "view": self}

    async def on_timeout(self) -> None:
        # check if disable_on_timeout is True then disable the buttons
        if self._disable_on_timeout:
            # loop through all buttons and disable them
            for item in self.children:
                item.disabled = True  # type: ignore

            # update the message
            assert self.message is not None  # so that the type checker doesn't complain
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        assert interaction.user is not None  # so that the type checker doesn't complain

        # always return True when we don't have the author_id set
        if not self._author_id:
            return True

        # if the user is the author of the message, allow the interaction
        return interaction.user.id == self._author_id


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("$"), intents=discord.Intents(guilds=True, messages=True)
        )

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


bot = Bot()


@bot.command()
async def paginate_embed(ctx):
    """Starts a menu to paginate through 3 different embeds."""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    # Creates a Paginator object
    vw = Paginator([page1, page2, page3], author_id=ctx.author.id)

    # Sends the paginator to the current channel
    await vw.send(ctx.channel)


@bot.command()
async def paginate_text(ctx):
    """Starts a menu to paginate through 3 different text."""
    # a list of 3 different strings
    pages = ["This is page 1", "This is page 2", "This is page 3"]

    # Creates a Paginator object with the list of strings as the pages
    # and the author as the author of the message, this is so the menu can only be used by the author. This is optional
    vw = Paginator(pages, author_id=ctx.author.id)
    await vw.send(ctx.channel)


@bot.command()
async def paginate_reply(ctx):
    """Starts a menu to paginate through 3 different embeds on the replied message."""

    # a list of 3 different strings
    pages = ["This is page 1", "This is page 2", "This is page 3"]

    # Creates a Paginator object
    # and the author as the author of the message, this is so the menu can only be used by the author. This is optional
    vw = Paginator(pages, author_id=ctx.author.id)

    # Replies to the passed message with the paginator
    await vw.send(ctx.message.reference.cached_message)


bot.run("TOKEN")
