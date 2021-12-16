from __future__ import annotations
from typing import Coroutine, Literal, Optional, Dict, Any, List, Union, Tuple, TypeVar


import discord
from discord.ext import commands

from discord.ui import view

MISSING = discord.utils.MISSING


class PaginatorButton(discord.ui.Button["Paginator"]):
    def __init__(
        self,
        *,
        emoji: Optional[Union[discord.PartialEmoji, str]] = None,
        label: Optional[str] = None,
        style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        position: int = MISSING,
    ) -> None:
        super().__init__(emoji=emoji, label=label, style=style)
        self._position: int = position

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None  # so that the type checker doesn't complain

        if self.custom_id == "stop_button":
            await self.view._stop_menu()
            return

        # Set the current_page attribute to th correct page

        if self.custom_id == "right_button":
            self.view.current_page += 1
        elif self.custom_id == "left_button":
            self.view.current_page -= 1
        elif self.custom_id == "first_button":
            self.view.current_page = 0
        elif self.custom_id == "last_button":
            self.view.current_page = self.view.max_pages - 1

        # Update the paginator

        # disable the buttons if needed

        if self.view.current_page == 0:
            self.view.FIRST_BUTTON.disabled = True
            self.view.LEFT_BUTTON.disabled = True
        else:
            self.view.FIRST_BUTTON.disabled = False
            self.view.LEFT_BUTTON.disabled = False

        if self.view.current_page >= self.view.max_pages - 1:
            self.view.LAST_BUTTON.disabled = True
            self.view.RIGHT_BUTTON.disabled = True
        else:
            self.view.LAST_BUTTON.disabled = False
            self.view.RIGHT_BUTTON.disabled = False

        # elif self.view.current_page >= self.view.max_pages - 1:

        keywords, _ = await self.view.handle_page_content()
        assert interaction.message is not None
        await interaction.message.edit(**keywords)


class Paginator(discord.ui.View):
    FIRST_BUTTON: PaginatorButton
    LAST_BUTTON: PaginatorButton
    LEFT_BUTTON: PaginatorButton
    RIGHT_BUTTON: PaginatorButton
    STOP_BUTTON: PaginatorButton

    def __init__(
        self,
        pages: Union[List[discord.Embed], List[str]],
        *,
        author_id: int = None,
        disable_on_timeout: bool = False,
        delete_message_after: bool = False,
        clear_after: bool = False,
        timeout: int = 180,
    ):

        # dict of default buttons
        DEFAULT_BUTTONS: Dict[Literal["first", "left", "right", "last", "stop"], PaginatorButton] = {
            "first": PaginatorButton(label="First", style=discord.ButtonStyle.primary, position=0),
            "left": PaginatorButton(label="Left", style=discord.ButtonStyle.primary, position=1),
            "stop": PaginatorButton(label="Stop", style=discord.ButtonStyle.danger, position=2),
            "right": PaginatorButton(label="Right", style=discord.ButtonStyle.primary, position=3),
            "last": PaginatorButton(label="Last", style=discord.ButtonStyle.primary, position=4),
        }

        super().__init__(timeout=timeout)

        # assign the basic attributes

        self._author_id = author_id
        self._disable_on_timeout = disable_on_timeout
        self._delete_message_after = delete_message_after
        self._clear_after = clear_after
        self.buttons: Dict[Literal["first", "left", "right", "last", "stop"], PaginatorButton] = DEFAULT_BUTTONS

        self.message: Optional[discord.Message] = None

        # for the pages
        self.pages: Union[List[discord.Embed], List[str]] = pages
        self.current_page: int = 0
        self.max_pages: int = len(self.pages)
        self.page_string = f"Page {self.current_page}/{self.max_pages}"

        # adds the buttons to the view
        self.add_buttons()

    def add_buttons(self):
        if all(b in ["first", "left", "right", "last", "stop"] for b in self.buttons.keys()) is False:
            raise ValueError("Paginator buttons must have a left, right and stop button")

        # no need to run a view and add buttons if there are no pages.
        if self.max_pages <= 1:
            self.stop()
            return

        button: PaginatorButton

        # loop through the buttons and adding them to the view
        for name, button in self.buttons.items():
            if not isinstance(button, PaginatorButton):
                raise TypeError(f"{button.__class__} is not a PaginatorButton")

            # set the custom_id
            button.custom_id = f"{name}_button"

            # setting the buttons as attributes for easy access.
            setattr(self, button.custom_id.upper(), button)

            if button.custom_id in ("first_button", "last_button") and self.max_pages <= 2:
                continue

            if button.custom_id in ("first_button", "left_button") and self.current_page <= 0:
                button.disabled = True

            if button.custom_id in ("last_button", "right_button") and self.current_page >= self.max_pages - 1:
                button.disabled = True

            self.add_item(button)

        self.__set_position()

    def __set_position(self) -> None:
        """Moves the buttons to the desired position"""
        button: PaginatorButton
        for button in self.children:  # type: ignore
            if button._position is not MISSING:
                self.children.insert(button._position, self.children.pop(self.children.index(button)))

    async def format_page(self, page: Union[discord.Embed, str]) -> Union[discord.Embed, str]:
        return page

    async def handle_page_content(
        self, kwargs: Optional[Any] = None
    ) -> Union[Tuple[Dict[str, Any], None], Tuple[Dict[str, Any], Dict[str, Any]], Tuple[dict, None]]:
        self.page_string: str = f"Page {self.current_page + 1}/{self.max_pages}"  # type: ignore

        # get page content aka see if it's an embed or string.
        keywords = await self.get_page_kwargs(self.current_page)

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

    async def get_page_kwargs(self, page_number: int) -> Optional[Dict[str, Any]]:

        # check if page is over the max pages and return None
        if page_number < 0 or page_number >= self.max_pages:
            return None

        # get the page
        page: Coroutine[Any, Any, Union[str, discord.Embed]] = await discord.utils.maybe_coroutine(
            self.format_page, self.pages[page_number]
        )
        # check if page is a string
        if isinstance(page, str):
            return {"content": page, "embed": None, "view": self}

        # check if the page is an embed
        elif isinstance(page, discord.Embed):
            return {"content": None, "embed": page, "view": self}

        # if the page is neither a string or an embed, raise an error
        else:
            raise TypeError(f"{page.__class__} is not a string or an embed.")

    async def on_timeout(self) -> None:
        await self._stop_menu()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        assert interaction.user is not None  # so that the type checker doesn't complain

        # always return True when we don't have the author_id set
        if not self._author_id:
            return True

        # if the user is the author of the message, allow the interaction
        return interaction.user.id == self._author_id

    async def _stop_menu(self):
        assert self.message is not None  # so that the type checker doesn't complain

        self.stop()

        if self._delete_message_after:
            await self.message.delete()
            return

        elif self._clear_after:
            await self.message.edit(view=None)
            return

        # check if disable_on_timeout is True then disable the buttons
        elif self._disable_on_timeout:
            # loop through all buttons and disable them
            for item in self.children:
                item.disabled = True  # type: ignore

            # update the message
            await self.message.edit(view=self)

        else:
            return

    # main way to send the menu
    async def send(
        self, send_to: Union[discord.abc.Messageable, discord.Message], *args: Any, **kwargs: Any
    ) -> discord.Message:

        # get the page content
        keywords, kwargs = await self.handle_page_content(kwargs)  # type: ignore

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

    @property
    def view(self):
        return self


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("$"), intents=discord.Intents(guilds=True, messages=True)
        )

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


bot = Bot()


class Yes(Paginator):
    def format_page(self, page):
        page.title = "yes"
        return page


@bot.command()
async def yes(ctx):
    """Starts a menu to paginate through 3 different embeds."""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    # Creates a Paginator object
    vw = Yes([page1, page2, page3], author_id=ctx.author.id)

    # Sends the paginator to the current channel
    await vw.send(ctx.channel)


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


bot.run("lol")
