from typing import Literal, Optional, Dict, Any, List, Union, Tuple
from discord.ext import commands
import discord

# Defines a custom button that contains the logic of the paginator.
# The ['Paginator'] bit is for type hinting purposes to tell your IDE or linter
# what the type of `self.view` is. It is not required.
class PaginatorButton(discord.ui.Button["Paginator"]):
    def __init__(
        self,
        *,
        emoji: Optional[Union[discord.PartialEmoji, str]] = None,
        label: Optional[str] = None,
        style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        position: Optional[int] = None,
    ) -> None:
        # It's possible to set either a label or emoji or both.
        # We added a custom parameter called "position" to set the position of the button.
        super().__init__(emoji=emoji, label=label, style=style)

        # Since a button must have either an or label, we raise if neither are set.
        if not emoji and not label:
            raise ValueError("A label or emoji must be provided.")

        # We need to do this to access the set position when adding the button to the paginator.
        self.position: Optional[int] = position

    # This is where we do the logic of the paginator, this is called when a button is clicked.
    async def callback(self, interaction: discord.Interaction):
        # You will see more of these in the example, this is for type hinting purposes to tell your IDE or linter that the attribute is not None.
        assert self.view is not None

        # Stop the paginator when the stop button is pressed.
        if self.custom_id == "stop_button":
            await self.view.stop()
            return

        # Set the current_page attribute in the View (Paginator class) to the correct page.
        if self.custom_id == "right_button":
            self.view.current_page += 1
        elif self.custom_id == "left_button":
            self.view.current_page -= 1
        elif self.custom_id == "first_button":
            self.view.current_page = 0
        elif self.custom_id == "last_button":
            self.view.current_page = self.view.max_pages - 1

        # Updates the page_string attribute in the View (Paginator class) to the correct page, this is used to display the current page / max pages.
        self.view.page_string: str = f"Page {self.view.current_page + 1}/{self.view.max_pages}"  # type: ignore
        # Sets the "page" button to be the current page.
        self.view.PAGE_BUTTON.label = self.view.page_string

        # Here we disable the buttons that are not needed on the current page and enable the ones that are.
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

        # Get the contents of the current page.
        page_kwargs, _ = await self.view.get_page_kwargs(self.view.current_page)
        assert interaction.message is not None and self.view.message is not None

        # If for whaterver reason editing the interaction message fails, we edit the paginator message instead.
        try:
            await interaction.message.edit(**page_kwargs)
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            await self.view.message.edit(**page_kwargs)


class Paginator(discord.ui.View):

    # This tells the IDE or linter that the attributes do exist and are of type 'PaginatorButton'.
    # This is not required
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
        disable_after: bool = False,
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
            # label="page" is a placeholder and is replaced with the correct string in _add_buttons
            "page": PaginatorButton(label="page", style=discord.ButtonStyle.primary, position=2),
            "stop": PaginatorButton(label="Stop", style=discord.ButtonStyle.danger, position=3),
            "right": PaginatorButton(label="Right", style=discord.ButtonStyle.primary, position=4),
            "last": PaginatorButton(label="Last", style=discord.ButtonStyle.primary, position=5),
        }

        # assign the basic attributes

        self.ctx: Optional[commands.Context] = ctx
        self.author_id: Optional[int] = author_id

        self._disable_after = disable_after
        self._delete_message_after = delete_message_after
        self._clear_after = clear_after
        self.buttons: Dict[str, Union[PaginatorButton, None]] = buttons or DEFAULT_BUTTONS
        self.message: Optional[discord.Message] = None

        # for the paginator
        self.pages: Union[List[discord.Embed], List[str]] = pages
        self.current_page: int = 0
        self.max_pages: int = len(self.pages)
        self.page_string: str = f"Page {self.current_page + 1}/{self.max_pages}"

        self._add_buttons(DEFAULT_BUTTONS)

    # Adds the buttons to the view.
    def _add_buttons(self, default_buttons: Dict[str, Union[PaginatorButton, None]]) -> None:
        # Stop the view if there is or less than 1 page.
        if self.max_pages <= 1:
            super().stop()
            return

        # Here we make sure that the dictionary of buttons contains the right keys and values.
        VALID_KEYS = ["first", "left", "right", "last", "stop", "page"]
        if all(b in VALID_KEYS for b in self.buttons.keys()) is False:
            raise ValueError(f"Buttons keys must be in: `{', '.join(VALID_KEYS)}`")

        if all(isinstance(b, PaginatorButton) or b is None for b in self.buttons.values()) is False:
            raise ValueError("Buttons values must be PaginatorButton instances or None.")

        # This tells the IDE or linter that the button is of type 'PaginatorButton' or None.
        # This is not required
        button: Union[PaginatorButton, None]

        # Loops through the default buttons.
        for name, button in default_buttons.items():
            # loop through the custom buttons.
            for custom_name, custom_button in self.buttons.items():
                # If the custom buttons dictonary replaces the default button, we set the button to the custom button.
                if name == custom_name:
                    button = custom_button

            # Don't add the button if it is None.
            if button is None:
                continue

            # Sets the custom_id of each button, this is not required but we use it to access the buttons more easily.
            button.custom_id = f"{name}_button"

            # Setting the buttons as attributes for easy access.
            # This is not required
            # An example of the usage is self.LEFT_BUTTON
            # self.LEFT_BUTTON.label = "Left"
            setattr(self, button.custom_id.upper(), button)

            # Set the page button to correct label.
            if button.custom_id == "page_button":
                button.label = self.page_string
                button.disabled = True

            # Check if there are less than or 2 pages.
            # Then 'continue' to the next iteration of the loop.
            # This basically means that the button will not be added to the view.
            # This is for "first" and "last" buttons.
            if button.custom_id in ("first_button", "last_button") and self.max_pages <= 2:
                continue

            # Check if the current_page is 0 or less.
            # Then sets the disables the "first" and "left" buttons.
            if button.custom_id in ("first_button", "left_button") and self.current_page <= 0:
                button.disabled = True

            # Check if the current_page is more than or max_pages.
            # Then disables the "last" and "right" buttons.
            if button.custom_id in ("last_button", "right_button") and self.current_page >= self.max_pages - 1:
                button.disabled = True

            # Add the button to the view
            self.add_item(button)

        # This is called after the loop.
        self._set_button_positions()

    # This is kinda hacky, but it works.
    def _set_button_positions(self) -> None:
        """Moves the buttons to the desired position"""

        button: PaginatorButton

        # Loops through all buttons in the view
        for button in self.children:  # type: ignore
            # Check if button.paginator is not None
            if button.position is not None:
                # This is the hacky part, it sets the position of the button by modifying the children list.
                # .insert takes index and the item to add at that index.
                # .pop takes the index of the item to remove and returns it.
                # .index takes the item and returns the index of it.
                self.children.insert(button.position, self.children.pop(self.children.index(button)))

    # This is called before the page is send, this can be used to format the page.
    # This is used by overriding it in a subclass.
    async def format_page(self, page: Union[discord.Embed, str]) -> Union[discord.Embed, str]:
        return page

    # Here is where the parsing of the page happens.
    # Check if it's an embed or string.
    # Remove any conflicting kwargs when sending the message.
    # And calls format_page().
    async def get_page_kwargs(
        self: "Paginator", page: int, send_kwargs: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[Literal["content", "embed", "view"], Union[discord.Embed, str, "Paginator", None]], Dict[str, Any]]:

        if send_kwargs is not None:
            # Remove any content and embeds provided via send because that will conflict with the page content.
            send_kwargs.pop("content", None)
            send_kwargs.pop("embed", None)
            send_kwargs.pop("embeds", None)

        # Here is where we call the format_page function.
        # Since format_page can be non-async, we use utils.maybe_coroutine.
        # utils.maybe_coroutine checks if the function is async and if not, it just returns the result.
        formatted_page: Union[str, discord.Embed, None] = await discord.utils.maybe_coroutine(self.format_page, self.pages[page])  # type: ignore

        # This will return True if the page is a string.
        if isinstance(formatted_page, str):
            # Add the page string to the page,
            formatted_page += f"\n\n{self.page_string}"
            return {"content": formatted_page, "embed": None, "view": self}, send_kwargs or {}

        # This will return True if the page is an embed.
        elif isinstance(formatted_page, discord.Embed):
            # Add the page string to the embed's footer
            formatted_page.set_footer(text=self.page_string)
            return {"content": None, "embed": formatted_page, "view": self}, send_kwargs or {}

        # If the page is neither a string or an embed, return empty dictonaries.
        else:
            return {}, send_kwargs or {}

    # We want to call out custom stop function on timeout.
    # We do that by overriding this function.
    async def on_timeout(self) -> None:
        await self.stop()

    # This is where the checking happens.
    # This is called on every button press.
    async def interaction_check(self, interaction: discord.Interaction):
        # Allow everyone if interaction.user or ctx or author_id is None.
        if not interaction.user or not self.ctx or not self.author_id:
            return True

        # check if author_id is passed and not ctx
        if self.author_id and not self.ctx:
            return interaction.user.id == self.author_id
        else:
            # Else use ctx to check for the author id and bot owner.
            if not interaction.user.id in {
                getattr(self.ctx.bot, "owner_id", None),
                self.ctx.author.id,
                *getattr(self.ctx.bot, "owner_ids", {}),
            }:
                return False

        # Return True if the above statements somehow didn't return.
        return True

    # This is called on timeout or when the user presses the stop button or when the paginator is stopped.
    async def stop(self):
        # Call the default stop method, don't want to mess with that.
        super().stop()

        assert self.message is not None

        # Here we check if the paginator should be deleted on stop/timeout (delete_message_after).
        # Or if the buttons should be removed (clear_after).
        # Or if the buttons should be disabled (disable_after).

        if self._delete_message_after:
            await self.message.delete()
            return

        elif self._clear_after:
            await self.message.edit(view=None)
            return

        elif self._disable_after:
            # Loop through all buttons and disable them.
            for item in self.children:
                item.disabled = True  # type: ignore

            # Update the message.
            await self.message.edit(view=self)

    # This is a special method that allows the paginator to be send in response to an interaction.
    async def send_as_interaction(
        self, interaction: discord.Interaction, ephemeral: bool = False, *args, **kwargs
    ) -> Optional[Union[discord.Message, discord.WebhookMessage]]:
        page_kwargs, send_kwargs = await self.get_page_kwargs(self.current_page, kwargs)
        if not interaction.response.is_done():
            send = interaction.response.send_message
        else:
            # We have to defer in order to use the followup webhook.
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

    # Main way to send the menu.
    async def send(
        self, send_to: Union[discord.abc.Messageable, discord.Message], *args: Any, **kwargs: Any
    ) -> discord.Message:

        # Get the page content
        page_kwargs, send_kwargs = await self.get_page_kwargs(self.current_page, kwargs)

        # Check if send_to is a message or channel. If it is a message we reply to it else we send it to the channel.
        if isinstance(send_to, discord.Message):
            # send_to is a message, so we reply to it.
            self.message = await send_to.reply(*args, **page_kwargs, **send_kwargs)  # type: ignore
        else:
            # send_to is a channel, so we send to it.
            self.message = await send_to.send(*args, **page_kwargs, **send_kwargs)  # type: ignore

        # Return the sent message.
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


class PaginateButton(discord.ui.View):
    def __init__(self, pages: list, *, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.pages = pages

    @discord.ui.button(label="Click me for a paginator!", style=discord.ButtonStyle.primary)
    async def my_button(self, button: discord.ui.Button, interaction: discord.Interaction):

        # Creates a Paginator object with the list of embeds as the pages and the author id.
        pag = Paginator(self.pages, author_id=interaction.user.id, disable_on_stop=True)  # type: ignore
        # Use the send_as_interaction method to send the paginator as an interaction to the user (ephemeral).
        await pag.send_as_interaction(interaction, ephemeral=True)


@bot.command()
async def paginate_button(ctx):
    """Starts a menu to paginate through 3 different embeds via a button."""
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    await ctx.send("Paginator with button example", view=PaginateButton([page1, page2, page3]))


class CustomPage(Paginator):
    def format_page(self, page):
        # Set "Nice Example" as title to every page (embed).
        page.title = "Nice Example"
        # Return the edited page for the paginator to send.
        return page


@bot.command()
async def paginate_custom(ctx):
    """Starts a menu to paginate through 3 different embeds with a custom page class that formats the page"""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    # Creates an instance of our custom page class and pass the pages to it.
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
    """Starts a menu with custom buttons to paginate through 3 different embeds."""
    # Create the pages
    page1 = discord.Embed(description="This is page 1")
    page2 = discord.Embed(description="This is page 2")
    page3 = discord.Embed(description="This is page 3")

    # Our dictionary with the buttons
    MY_BUTTONS = {
        "first": PaginatorButton(emoji="⏮️", style=discord.ButtonStyle.primary, position=0),
        "left": PaginatorButton(emoji="⬅️", style=discord.ButtonStyle.primary, position=1),
        "stop": None,  # We don't want to stop button.
        "right": PaginatorButton(emoji="➡️", style=discord.ButtonStyle.primary, position=3),
        "last": PaginatorButton(emoji="⏭️", style=discord.ButtonStyle.primary, position=4),
    }
    # Creates a Paginator object and pass our buttons to it.
    vw = Paginator([page1, page2, page3], ctx=ctx, buttons=MY_BUTTONS)

    # Sends the paginator to the current channel
    await vw.send(ctx.channel)


bot.run("token")
