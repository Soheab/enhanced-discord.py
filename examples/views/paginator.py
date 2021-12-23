from __future__ import annotations
from typing import Literal, Optional, Dict, Any, List, Union, Tuple


import discord
from discord.ext import commands


class PaginatorButton(discord.ui.Button["Paginator"]):
    def __init__(
        self,
        *,
        emoji: Optional[Union[discord.PartialEmoji, str]] = None,
        label: Optional[str] = None,
        style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        position: Optional[int] = None,
    ) -> None:
        super().__init__(emoji=emoji, label=label, style=style)
        self.position: Optional[int] = position

    # this is where we handle the button clicks and page changes
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None  # so that the type checker doesn't complain

        # stop the paginator when the stop button is pressed
        if self.custom_id == "stop_button":
            await self.view.stop()
            return

        # Set the current_page attribute to the correct page

        if self.custom_id == "right_button":
            self.view.current_page += 1
        elif self.custom_id == "left_button":
            self.view.current_page -= 1
        elif self.custom_id == "first_button":
            self.view.current_page = 0
        elif self.custom_id == "last_button":
            self.view.current_page = self.view.max_pages - 1

        # update the page_string attribute
        self.view.page_string: str = f"Page {self.view.current_page + 1}/{self.view.max_pages}"  # type: ignore
        # update the page button
        self.view.PAGE_BUTTON.label = self.view.page_string

        # Update the paginator

        # disable the buttons if needed else enable them

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

        # get the page content to send
        page_kwargs, _ = await self.view.get_page_kwargs(self.view.current_page)
        assert (
            interaction.message is not None and self.view.message is not None
        )  # so that the type checker doesn't complain

        # edit the message
        try:
            await interaction.message.edit(**page_kwargs)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            await self.view.message.edit(**page_kwargs)


class Paginator(discord.ui.View):

    # this is for linter purposes because we want to access them in the button callback
    FIRST_BUTTON: PaginatorButton
    LAST_BUTTON: PaginatorButton
    LEFT_BUTTON: PaginatorButton
    RIGHT_BUTTON: PaginatorButton
    STOP_BUTTON: PaginatorButton
    PAGE_BUTTON: PaginatorButton

    def __init__(
        self,
        pages: Union[List[discord.Embed], List[str]],
        ctx: Optional[commands.Context] = None,
        author_id: Optional[int] = None,
        *,
        buttons: Dict[str, Union[PaginatorButton, None]] = {},
        disable_on_stop: bool = False,
        delete_message_after: bool = False,
        clear_after: bool = False,
        timeout: int = 180,
    ):
        # this is required for the view to work
        super().__init__(timeout=timeout)

        # dictonary of default buttons
        DEFAULT_BUTTONS: Dict[str, Union[PaginatorButton, None]] = {
            "first": PaginatorButton(label="First", style=discord.ButtonStyle.primary, position=0),
            "left": PaginatorButton(label="Left", style=discord.ButtonStyle.primary, position=1),
            "page": PaginatorButton(label="page", style=discord.ButtonStyle.primary, position=2),
            "stop": PaginatorButton(label="Stop", style=discord.ButtonStyle.danger, position=3),
            "right": PaginatorButton(label="Right", style=discord.ButtonStyle.primary, position=4),
            "last": PaginatorButton(label="Last", style=discord.ButtonStyle.primary, position=5),
        }

        # assign the basic attributes

        self.ctx: Optional[commands.Context] = ctx
        self.author_id: Optional[int] = author_id

        self._disable_on_stop = disable_on_stop
        self._delete_message_after = delete_message_after
        self._clear_after = clear_after
        self.buttons: Dict[str, Union[PaginatorButton, None]] = buttons or DEFAULT_BUTTONS

        self.message: Optional[discord.Message] = None

        # for the paginator
        self.pages: Union[List[discord.Embed], List[str]] = pages
        self.current_page: int = 0
        self.max_pages: int = len(self.pages)
        self.page_string: str = f"Page {self.current_page + 1}/{self.max_pages}"

        # adds the buttons to the view
        self._add_buttons(DEFAULT_BUTTONS)

    # this is where we add the buttons to the view, called in the __init__
    def _add_buttons(self, default_buttons: Dict[str, Union[PaginatorButton, None]]) -> None:

        # this is to check if the dictonary has the right keys
        VALID_KEYS = ["first", "left", "right", "last", "stop", "page"]
        if all(b in VALID_KEYS for b in self.buttons.keys()) is False:
            raise ValueError(f"Buttons keys must be in: `{', '.join(VALID_KEYS)}`")

        # this is to check if the dictonary has the right values
        if all(isinstance(b, PaginatorButton) or b is None for b in self.buttons.values()) is False:
            raise ValueError("Buttons values must be PaginatorButton instances or None.")

        # no need to run a view and add buttons if there are no pages.
        if self.max_pages <= 1:
            super().stop()
            return

        # this is for typing purposes
        button: Union[PaginatorButton, None]

        # loop through the buttons and adding them to the view

        # loop through the default buttons
        for name, button in default_buttons.items():

            # loop through the custom buttons
            for custom_name, custom_button in self.buttons.items():

                # if the custom buttons dictonary has a button for the default button, use it
                if name == custom_name:
                    button = custom_button

            # if the dictonary value is None, dont add it
            if button is None:
                continue

            # set the custom_id, this is for easy access/edit in the button callback
            button.custom_id = f"{name}_button"

            # setting the buttons as attributes for easy access.
            setattr(self, button.custom_id.upper(), button)

            # set the label of the page button and disable it
            if button.custom_id == "page_button":
                button.label = self.page_string
                button.disabled = True

            # this checks if there are less than or 2 pages, don't add the first and last buttons
            if button.custom_id in ("first_button", "last_button") and self.max_pages <= 2:
                continue

            # this checks if the current_page is 0 or less, disable the first and left button
            if button.custom_id in ("first_button", "left_button") and self.current_page <= 0:
                button.disabled = True

            # this checks if the current_page is the max_pages or more, disable the last and right button
            if button.custom_id in ("last_button", "right_button") and self.current_page >= self.max_pages - 1:
                button.disabled = True

            # add the button to the view
            self.add_item(button)

        # call the function to set the buttons to the desired positions
        self._set_button_positions()

    # this is kinda hacky, but it works
    def _set_button_positions(self) -> None:
        """Moves the buttons to the desired position"""

        # this is for typing purposes
        button: PaginatorButton

        # loop through all buttons in the view
        for button in self.children:  # type: ignore
            # check is button.paginator is not None
            if button.position is not None:
                # this is the hacky part, it sets the position of the button
                # .insert takes index and the item to add at that index
                # and .pop takes the index of the item to remove and remove and returns it
                # and .index takes the item and returns the index of the item
                self.children.insert(button.position, self.children.pop(self.children.index(button)))

    # this is for users to override to easily format their page
    async def format_page(self, page: Union[discord.Embed, str]) -> Union[discord.Embed, str]:
        return page

    # this is where we check the page and return the things to send it
    async def get_page_kwargs(
        self: "Paginator", page: int, send_kwargs: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[Literal["content", "embed", "view"], Union[discord.Embed, str, "Paginator", None]], Dict[str, Any]]:

        # check if send_kwargs are passed
        if send_kwargs is not None:
            # remove any content and embeds provided via send because that will conflict with the page content
            send_kwargs.pop("content", None)
            send_kwargs.pop("embed", None)
            send_kwargs.pop("embeds", None)

        # here is where we call the format_page function
        # since the format_page can be non-async, we use utils.maybe_coroutine
        # utils.maybe_coroutine checks if the function is async and if not, it just returns the result
        formatted_page: Union[str, discord.Embed, None] = await discord.utils.maybe_coroutine(self.format_page, self.pages[page])  # type: ignore

        # check if page is a string
        if isinstance(formatted_page, str):
            # add the page string to the page
            formatted_page += f"\n\n{self.page_string}"
            return {"content": formatted_page, "embed": None, "view": self}, send_kwargs or {}

        # check if the page is an embed
        elif isinstance(formatted_page, discord.Embed):
            # add the page string to the embed's footer
            formatted_page.set_footer(text=self.page_string)
            return {"content": None, "embed": formatted_page, "view": self}, send_kwargs or {}

        # if the page is neither a string or an embed, return empty dictonaries
        else:
            return {}, send_kwargs or {}

    # call out custom method on timeout
    async def on_timeout(self) -> None:
        await self.stop()

    # here is where check who can interact with the menu
    async def interaction_check(self, interaction: discord.Interaction):
        # allow everyone if interaction.user or ctx or author_id is None
        if not interaction.user or not self.ctx or not self.author_id:
            return True

        # check if author_id is passed and not ctx
        if self.author_id and not self.ctx:
            return interaction.user.id == self.author_id
        else:
            # else use ctx to check for the author id and bot owner
            if not interaction.user.id in {
                getattr(self.ctx.bot, "owner_id", None),
                self.ctx.author.id,
                *getattr(self.ctx.bot, "owner_ids", {}),
            }:
                return False

        # return True if the above statement somehow didn't run
        return True

    # our custom stop method
    async def stop(self):
        # call the default stop method
        super().stop()

        assert self.message is not None  # so that the type checker doesn't complain

        # delete the message if delete_message_after is True
        if self._delete_message_after:
            await self.message.delete()
            return

        # remove the view if clear_after is True
        elif self._clear_after:
            await self.message.edit(view=None)
            return

        # disable the buttons if disable_on_stop is True
        elif self._disable_on_stop:
            # loop through all buttons and disable them
            for item in self.children:
                item.disabled = True  # type: ignore

            # update the message
            await self.message.edit(view=self)

        else:
            return

    # this is a special method that allows the paginator to be send in response to an interaction
    async def send_as_interaction(
        self, interaction: discord.Interaction, ephemeral: bool = False, *args, **kwargs
    ) -> Optional[Union[discord.Message, discord.WebhookMessage]]:
        page_kwargs, send_kwargs = await self.get_page_kwargs(self.current_page, kwargs)
        if not interaction.response.is_done():
            send = interaction.response.send_message
        else:
            # We have to defer in order to use the followup webhook
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=ephemeral)

            send_kwargs["wait"] = True
            send = interaction.followup.send

        ret = await send(*args, ephemeral=ephemeral, **page_kwargs, **send_kwargs)  # type: ignore

        if not ret:
            try:
                self.message = await interaction.original_message()
            except (discord.ClientException, discord.HTTPException):
                self.message = None
        else:
            self.message = ret

        return self.message

    # main way to send the menu
    async def send(
        self, send_to: Union[discord.abc.Messageable, discord.Message], *args: Any, **kwargs: Any
    ) -> discord.Message:

        # get the page content
        page_kwargs, send_kwargs = await self.get_page_kwargs(self.current_page, kwargs)

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


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("$"), intents=discord.Intents(guilds=True, messages=True)
        )

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")  # type: ignore
        print("------")


bot = Bot()


class CustomPage(Paginator):
    def format_page(self, page):
        # add "Nice Example" as title to every page
        page.title = "Nice Example"
        # return the edited page for the paginator to send
        return page


@bot.command()
async def yes(ctx):
    """Starts a menu to paginate through 3 different embeds with a custom page class that formats the page"""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    # Creates a Paginator object
    vw = CustomPage([page1, page2, page3], ctx=ctx)

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
    vw = Paginator([page1, page2, page3], ctx=ctx)
    # Sends the paginator to the current channel
    await vw.send(ctx.channel)


@bot.command()
async def paginate_text(ctx):
    """Starts a menu to paginate through 3 different text."""
    # a list of 3 different strings
    pages = ["This is page 1", "This is page 2", "This is page 3"]

    # Creates a Paginator object with the list of strings as the pages
    # and the author as the author of the message, this is so the menu can only be used by the author. This is optional
    vw = Paginator(pages, ctx=ctx)
    await vw.send(ctx.channel)


@bot.command()
async def paginate_reply(ctx):
    """Starts a menu to paginate through 3 different embeds on the replied message."""

    # a list of 3 different strings
    pages = ["This is page 1", "This is page 2", "This is page 3"]

    # Creates a Paginator object
    # and the author as the author of the message, this is so the menu can only be used by the author. This is optional
    vw = Paginator(pages, ctx=ctx)

    # Replies to the passed message with the paginator
    await vw.send(ctx.message.reference.cached_message)


@bot.command()
async def paginate_custom_buttons(ctx):
    """Starts a menu to paginate through 3 different embeds."""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    MY_BUTTONS = {
        "first": PaginatorButton(emoji="⏮️", style=discord.ButtonStyle.primary, position=0),
        "left": PaginatorButton(emoji="⬅️", style=discord.ButtonStyle.primary, position=1),
        "stop": None,  # PaginatorButton(label="⏹️", style=discord.ButtonStyle.danger, position=4),
        "right": PaginatorButton(emoji="➡️", style=discord.ButtonStyle.primary, position=3),
        "last": PaginatorButton(emoji="⏭️", style=discord.ButtonStyle.primary, position=4),
    }
    # Creates a Paginator object
    vw = Paginator([page1, page2, page3], ctx=ctx, buttons=MY_BUTTONS)
    # Sends the paginator to the current channel
    await vw.send(ctx.channel)


class PaginateButton(discord.ui.View):
    def __init__(self, pages: list, *, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.pages = pages

    @discord.ui.button(label="Click me for a paginator!", style=discord.ButtonStyle.primary)
    async def my_button(self, button: discord.ui.Button, interaction: discord.Interaction):

        # Creates a Paginator object
        vw = Paginator(self.pages, author_id=interaction.user.id, disable_on_stop=True)  # type: ignore
        await vw.send_as_interaction(interaction, ephemeral=True)


@bot.command()
async def paginate_button(ctx):
    """Starts a menu to paginate through 3 different embeds."""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    await ctx.send("Paginator with button example", view=PaginateButton([page1, page2, page3]))


bot.run("TOKEN")
