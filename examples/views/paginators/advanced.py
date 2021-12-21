from __future__ import annotations
from typing import Coroutine, Literal, Optional, Dict, Any, List, Union, Tuple, TypeVar


import discord
from discord.ext import commands

from discord.ui import view

MISSING = discord.utils.MISSING
P = TypeVar("P", bound="Paginator")


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

        page_kwargs = await self.view.get_page_kwargs(self.view.current_page)
        assert interaction.message is not None
        await interaction.message.edit(**page_kwargs)


class Paginator(discord.ui.View):
    FIRST_BUTTON: PaginatorButton
    LAST_BUTTON: PaginatorButton
    LEFT_BUTTON: PaginatorButton
    RIGHT_BUTTON: PaginatorButton
    STOP_BUTTON: PaginatorButton

    def __init__(
        self,
        pages: Union[List[discord.Embed], List[str]],
        ctx: Optional[commands.Context] = MISSING,
        *,
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

        self.ctx: Optional[commands.Context] = ctx
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
        self._add_buttons()

    def _add_buttons(self):
        if all(b in ["first", "left", "right", "last", "stop"] for b in self.buttons.keys()) is False:
            raise ValueError("Buttons keys must be one of 'first', 'left', 'right', 'last', 'stop'")

        if all(isinstance(b, PaginatorButton) for b in self.buttons.values()) is False:
            raise ValueError("Buttons values must be PaginatorButton instances")

        # no need to run a view and add buttons if there are no pages.
        if self.max_pages <= 1:
            super().stop()
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

        self._set_button_positions()

    def _set_button_positions(self) -> None:
        """Moves the buttons to the desired position"""
        button: PaginatorButton
        for button in self.children:  # type: ignore
            if button._position is not MISSING:
                self.children.insert(button._position, self.children.pop(self.children.index(button)))

    async def format_page(self, page: Union[discord.Embed, str]) -> Union[discord.Embed, str]:
        return page

    async def get_page_kwargs(
        self: P, page: int, send_kwargs: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[Literal["content", "embed", "view"], Union[discord.Embed, str, P, None]], Dict[str, Any]]:

        if send_kwargs is not None:
            # remove any content and embeds provided via send because that will conflict with the page content
            try:
                del send_kwargs["content"]
                del send_kwargs["embed"]
                del send_kwargs["embeds"]
            except KeyError:
                pass

        self.page_string: str = f"Page {self.current_page + 1}/{self.max_pages}"  # type: ignore

        formatted_page: Union[str, discord.Embed, None] = await discord.utils.maybe_coroutine(self.format_page, self.pages[page])  # type: ignore

        # check if page is a string
        if isinstance(formatted_page, str):
            formatted_page += f"\n\n{self.page_string}"
            return {"content": formatted_page, "embed": None, "view": self}, send_kwargs or {}

        # check if the page is an embed
        elif isinstance(formatted_page, discord.Embed):
            formatted_page.set_footer(text=self.page_string)
            return {"content": None, "embed": formatted_page, "view": self}, send_kwargs or {}

        # if the page is neither a string or an embed, raise an error
        else:
            return {}, send_kwargs or {}

    async def on_timeout(self) -> None:
        await self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user or not self.ctx:
            return True

        if not interaction.user.id in {
            getattr(self.ctx.bot, "owner_id", None),
            self.ctx.author.id,
            *getattr(self.ctx.bot, "owner_ids", {}),
        }:
            return False

        return True

    async def stop(self):
        super().stop()

        assert self.message is not None  # so that the type checker doesn't complain

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

    async def send_with_interaction(self, interaction: discord.Interaction, *args, **kwargs) -> None:
        page_kwargs, send_kwargs = await self.get_page_kwargs(self.current_page, kwargs)

        await interaction.response.send_message(*args, **page_kwargs, **send_kwargs)

    # main way to send the menu
    async def send(
        self, send_to: Union[discord.abc.Messageable, discord.Message], *args: Any, **kwargs: Any
    ) -> discord.Message:

        # get the page content
        page_kwargs, send_kwargs = await self.get_page_kwargs(self.current_page, kwargs)

        # raise if send_to is None
        if not send_to:
            raise ValueError("send_to can not be None")

        # check if send_to is a message or channel. If it is a message we reply to it else we send it to the channel
        if isinstance(send_to, discord.Message):
            # send_to is a message, so we reply to it
            self.message = await send_to.reply(*args, **page_kwargs, **send_kwargs)  # type: ignore
        else:
            # send_to is a channel, so we send it
            self.message = await send_to.send(*args, **page_kwargs, **send_kwargs)  # type: ignore

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
