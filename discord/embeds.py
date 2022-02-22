"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from typing import Any, Dict, Final, Iterable, List, Mapping, Protocol, TYPE_CHECKING, Tuple, Type, TypeVar, Union

from . import utils
from .colour import Colour

__all__: Tuple[str, ...] = (
    "Embed",
    "EmbedAuthor",
    "EmbedField",
    "EmbedFooter",
)


class _EmptyEmbed:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Embed.Empty"

    def __len__(self) -> int:
        return 0


EmptyEmbed: Final = _EmptyEmbed()


class EmbedProxy:
    def __init__(self, layer: Dict[str, Any]):
        self.__dict__.update(layer)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __repr__(self) -> str:
        inner = ", ".join((f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")))
        return f"EmbedProxy({inner})"

    def __getattr__(self, attr: str) -> _EmptyEmbed:
        return EmptyEmbed


E = TypeVar("E", bound="Embed")

if TYPE_CHECKING:
    from discord.types.embed import Embed as EmbedData, EmbedType

    T = TypeVar("T")
    MaybeEmpty = Union[T, _EmptyEmbed]

    class _EmbedFooterProxy(Protocol):
        text: MaybeEmpty[str]
        icon_url: MaybeEmpty[str]

    class _EmbedFieldProxy(Protocol):
        name: MaybeEmpty[str]
        value: MaybeEmpty[str]
        inline: bool

    class _EmbedMediaProxy(Protocol):
        url: MaybeEmpty[str]
        proxy_url: MaybeEmpty[str]
        height: MaybeEmpty[int]
        width: MaybeEmpty[int]

    class _EmbedVideoProxy(Protocol):
        url: MaybeEmpty[str]
        height: MaybeEmpty[int]
        width: MaybeEmpty[int]

    class _EmbedProviderProxy(Protocol):
        name: MaybeEmpty[str]
        url: MaybeEmpty[str]

    class _EmbedAuthorProxy(Protocol):
        name: MaybeEmpty[str]
        url: MaybeEmpty[str]
        icon_url: MaybeEmpty[str]
        proxy_icon_url: MaybeEmpty[str]


@dataclass
class EmbedField:
    """Represents an :class:`Embed` field.

        .. container:: operations

        .. describe:: len(x)

            Returns the total size of the field
            (the length of the name plus the length of the value).

    .. versionadded:: 2.0

    Attributes
    ----------
    name: :class:`str`
        The name of the field.
    value: :class:`str`
        The value of the field.
    inline: :class:`bool`
        Whether the field should display inline.
    """

    name: str
    value: str
    inline: bool = False

    def __len__(self) -> int:
        return len(self.name) + len(self.value)

    def to_dict(self) -> Dict[str, Union[str, bool]]:
        return {
            "name": self.name,
            "value": self.value,
            "inline": self.inline,
        }

    def _edit(self, *, name: str, value: str, inline: bool) -> None:
        self.name = name
        self.value = value
        self.inline = inline


@dataclass(frozen=True)
class EmbedFooter:
    """Represents an :class:`Embed` footer.

        .. container:: operations

        .. describe:: len(x)

            Returns the total size of the footer (the length of the text).

    .. versionadded:: 2.0

    Attributes
    ----------
    text: Optional[:class:`str`]
        The footer text. If any else :class:`Embed.Empty`.
    icon_url: Optional[:class:`str`]
        The URL of the footer icon. If any else :class:`Embed.Empty`.
    proxy_icon_url: Optional[:class:`str`]
        The proxy URL of the footer icon. If any else :class:`Embed.Empty`.
    """

    text: MaybeEmpty[str] = EmptyEmbed
    icon_url: MaybeEmpty[str] = EmptyEmbed
    proxy_icon_url: MaybeEmpty[str] = EmptyEmbed

    def __len__(self) -> int:
        return len(self.text)

    def to_dict(self) -> Dict[str, str]:
        payload: Dict[str, Any] = {}
        if self.text is not EmptyEmbed:
            payload["text"] = self.text
        if self.icon_url is not EmptyEmbed:
            payload["icon_url"] = self.icon_url

        return payload


@dataclass(frozen=True)
class EmbedAuthor:
    """Represents an :class:`Embed` author.

        .. container:: operations

        .. describe:: len(x)

            Returns the total size of the author (the length of the name).

    .. versionadded:: 2.0

    Attributes
    ----------
    name: Optional[:class:`str`]
        The name of the author. If any else :class:`Embed.Empty`.
    url: Optional[:class:`str`]
        The URL of the author. If any else :class:`Embed.Empty`.
    icon_url: Optional[:class:`str`]
        The URL of the author icon. If any else :class:`Embed.Empty`.
    proxy_icon_url: Optional[:class:`str`]
        The proxy URL of the author icon. If any else :class:`Embed.Empty`.
    """

    name: str
    url: MaybeEmpty[str] = EmptyEmbed
    icon_url: MaybeEmpty[str] = EmptyEmbed
    proxy_icon_url: MaybeEmpty[str] = EmptyEmbed

    def __len__(self) -> int:
        return len(self.name)

    def to_dict(self) -> Dict[str, str]:
        payload: Dict[str, Any] = {}
        if self.name is not EmptyEmbed:
            payload["name"] = self.name
        if self.icon_url is not EmptyEmbed:
            payload["icon_url"] = self.icon_url
        if self.url is not EmptyEmbed:
            payload["url"] = self.url

        return payload


class Embed:
    """Represents a Discord embed.

    .. container:: operations

        .. describe:: len(x)

            Returns the total size of the embed.
            Useful for checking if it's within the 6000 character limit.

        .. describe:: bool(b)

            Returns whether the embed has any data set.

            .. versionadded:: 2.0

    Certain properties return an ``EmbedProxy``, a type
    that acts similar to a regular :class:`dict` except using dotted access,
    e.g. ``embed.author.icon_url``. If the attribute
    is invalid or empty, then a special sentinel value is returned,
    :attr:`Embed.Empty`.

    For ease of use, all parameters that expect a :class:`str` are implicitly
    casted to :class:`str` for you.

    Attributes
    -----------
    title: :class:`str`
        The title of the embed.
        This can be set during initialisation.
    type: :class:`str`
        The type of embed. Usually "rich".
        This can be set during initialisation.
        Possible strings for embed types can be found on discord's
        `api docs <https://discord.com/developers/docs/resources/channel#embed-object-embed-types>`_
    description: :class:`str`
        The description of the embed.
        This can be set during initialisation.
    url: :class:`str`
        The URL of the embed.
        This can be set during initialisation.
    timestamp: :class:`datetime.datetime`
        The timestamp of the embed content. This is an aware datetime.
        If a naive datetime is passed, it is converted to an aware
        datetime with the local timezone.
    colour: Union[:class:`Colour`, :class:`int`]
        The colour code of the embed. Aliased to ``color`` as well.
        This can be set during initialisation.
    Empty
        A special sentinel value used by ``EmbedProxy`` and this class
        to denote that the value or attribute is empty.
    """

    __slots__ = (
        "title",
        "url",
        "type",
        "_timestamp",
        "_colour",
        "_image",
        "_thumbnail",
        "_video",
        "_provider",
        "_fields",
        "_footer",
        "_author",
        "description",
    )

    Empty: Final = EmptyEmbed

    def __init__(
        self,
        *,
        colour: Union[int, Colour, _EmptyEmbed] = EmptyEmbed,
        color: Union[int, Colour, _EmptyEmbed] = EmptyEmbed,
        title: MaybeEmpty[Any] = EmptyEmbed,
        type: EmbedType = "rich",
        url: MaybeEmpty[Any] = EmptyEmbed,
        description: MaybeEmpty[Any] = EmptyEmbed,
        timestamp: datetime.datetime = None,
        image: MaybeEmpty[str] = EmptyEmbed,
        thumbnail: MaybeEmpty[str] = EmptyEmbed,
        fields: Iterable[EmbedField] = [],
        footer: MaybeEmpty[EmbedFooter] = EmptyEmbed,
        author: MaybeEmpty[EmbedAuthor] = EmptyEmbed,
    ):

        self.colour = colour if colour is not EmptyEmbed else color
        self.title = title
        self.type = type
        self.url = url
        self.description = description

        if timestamp:
            self.timestamp = timestamp
        if fields:
            self.fields = list(fields)

        if self.title is not EmptyEmbed:
            self.title = str(self.title)
        if self.description is not EmptyEmbed:
            self.description = str(self.description)
        if self.url is not EmptyEmbed:
            self.url = str(self.url)
        if image is not EmptyEmbed:
            self.image = str(image)
        if thumbnail is not EmptyEmbed:
            self.thumbnail = str(thumbnail)
        if footer is not EmptyEmbed:
            self.footer = footer
        if author is not EmptyEmbed:
            self.author = author

    @classmethod
    def from_dict(cls: Type[E], data: Mapping[str, Any]) -> E:
        """Converts a :class:`dict` to a :class:`Embed` provided it is in the
        format that Discord expects it to be in.

        You can find out about this format in the `official Discord documentation`__.

        .. _DiscordDocs: https://discord.com/developers/docs/resources/channel#embed-object

        __ DiscordDocs_

        Parameters
        -----------
        data: :class:`dict`
            The dictionary to convert into an embed.
        """
        # we are bypassing __init__ here since it doesn't apply here
        self: E = cls.__new__(cls)

        # fill in the basic fields

        self.title = data.get("title", EmptyEmbed)
        self.type = data.get("type", EmptyEmbed)
        self.description = data.get("description", EmptyEmbed)
        self.url = data.get("url", EmptyEmbed)

        if self.title is not EmptyEmbed:
            self.title = str(self.title)

        if self.description is not EmptyEmbed:
            self.description = str(self.description)

        if self.url is not EmptyEmbed:
            self.url = str(self.url)

        # try to fill in the more rich fields

        try:
            self._colour = Colour(value=data["color"])
        except KeyError:
            pass

        try:
            self._timestamp = utils.parse_time(data["timestamp"])
        except KeyError:
            pass

        for class_attr in ("footer", "author", "fields"):
            if class_attr not in data:
                continue

            attr_to_dataclass: Dict[str, Any] = {
                "footer": EmbedFooter,
                "author": EmbedAuthor,
                "fields": EmbedField,
            }
            if class_attr == "fields":
                self._fields = [attr_to_dataclass[class_attr](**field) for field in data[class_attr]]
            else:
                setattr(self, f"_{class_attr}", attr_to_dataclass[class_attr](**data[class_attr]))

        for attr in ("thumbnail", "video", "provider", "image"):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, "_" + attr, value)

        return self

    def copy(self: E) -> E:
        """Returns a shallow copy of the embed."""
        return self.__class__.from_dict(self.to_dict())

    def __len__(self) -> int:
        total = len(self.title) + len(self.description)
        for attr in ("footer", "author", "fields"):
            attr_value = getattr(self, attr, None)
            if not attr_value or attr_value is EmptyEmbed:
                continue

            if attr == "fields":
                for field in attr_value:
                    total += len(field)
            else:
                total += len(attr_value)

        return total

    def __bool__(self) -> bool:
        return any(
            (
                self.title,
                self.url,
                self.description,
                self.colour,
                self.fields,
                self.timestamp,
                self.author,
                self.thumbnail,
                self.footer,
                self.image,
                self.provider,
                self.video,
            )
        )

    @property
    def colour(self) -> MaybeEmpty[Colour]:
        return getattr(self, "_colour", EmptyEmbed)

    @colour.setter
    def colour(self, value: Union[int, Colour, _EmptyEmbed]):  # type: ignore
        if isinstance(value, (Colour, _EmptyEmbed)):
            self._colour = value
        elif isinstance(value, int):
            self._colour = Colour(value=value)
        else:
            raise TypeError(
                f"Expected discord.Colour, int, or Embed.Empty but received {value.__class__.__name__} instead."
            )

    color = colour

    @colour.deleter
    def colour(self) -> None:
        try:
            del self._colour
        except AttributeError:
            pass

    @property
    def timestamp(self) -> MaybeEmpty[datetime.datetime]:
        return getattr(self, "_timestamp", EmptyEmbed)

    @timestamp.setter
    def timestamp(self, value: MaybeEmpty[datetime.datetime]):
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                value = value.astimezone()
            self._timestamp = value
        elif isinstance(value, _EmptyEmbed):
            self._timestamp = value
        else:
            raise TypeError(f"Expected datetime.datetime or Embed.Empty received {value.__class__.__name__} instead")

    @timestamp.deleter
    def timestamp(self) -> None:
        try:
            del self._timestamp
        except AttributeError:
            pass

    @property
    def footer(self) -> EmbedFooter:
        """:class:`EmbedFooter`: The footer of the embed."""
        return getattr(self, "_footer", EmbedFooter())  # type: ignore

    @footer.setter
    def footer(self, footer: MaybeEmpty[EmbedFooter], /) -> None:
        if footer is EmptyEmbed:
            del self._footer
            return

        if not isinstance(footer, EmbedFooter):
            raise TypeError(f"Expected EmbedFooter received {footer.__class__.__name__} instead")

        self._footer = footer

    @footer.deleter
    def footer(self) -> None:
        try:
            del self._footer
        except AttributeError:
            pass

    def set_footer(self: E, *, text: MaybeEmpty[Any] = EmptyEmbed, icon_url: MaybeEmpty[Any] = EmptyEmbed) -> E:
        """Sets the footer for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        text: :class:`str`
            The footer text.
        icon_url: :class:`str`
            The URL of the footer icon. Only HTTP(S) is supported.
        """
        fields = {}
        if text is not EmptyEmbed:
            fields["text"] = str(text)

        if icon_url is not EmptyEmbed:
            fields["icon_url"] = str(icon_url)

        self._footer = EmbedFooter(**fields)
        return self

    def remove_footer(self: E) -> E:
        """Clears embed's footer information.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 2.0
        """
        del self.footer
        return self

    @property
    def image(self) -> _EmbedMediaProxy:
        """Returns an ``EmbedProxy`` denoting the image contents.

        Possible attributes you can access are:

        - ``url``
        - ``proxy_url``
        - ``width``
        - ``height``

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, "_image", {}))  # type: ignore

    @image.setter
    def image(self, url: Any):
        if url is EmptyEmbed:
            del self.image
        else:
            self._image = {"url": str(url)}

    @image.deleter
    def image(self):
        try:
            del self._image
        except AttributeError:
            pass

    def set_image(self: E, *, url: MaybeEmpty[Any]) -> E:
        """Sets the image for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionchanged:: 1.4
            Passing :attr:`Empty` removes the image.

        Parameters
        -----------
        url: :class:`str`
            The source URL for the image. Only HTTP(S) is supported.
        """

        self.image = url
        return self

    @property
    def thumbnail(self) -> _EmbedMediaProxy:
        """Returns an ``EmbedProxy`` denoting the thumbnail contents.

        Possible attributes you can access are:

        - ``url``
        - ``proxy_url``
        - ``width``
        - ``height``

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, "_thumbnail", {}))  # type: ignore

    @thumbnail.setter
    def thumbnail(self, url: Any):
        if url is EmptyEmbed:
            del self.thumbnail
        else:
            self._thumbnail = {"url": str(url)}

    @thumbnail.deleter
    def thumbnail(self):
        try:
            del self._thumbnail
        except AttributeError:
            pass

    def set_thumbnail(self, *, url: MaybeEmpty[Any]):
        """Sets the thumbnail for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionchanged:: 1.4
            Passing :attr:`Empty` removes the thumbnail.

        Parameters
        -----------
        url: :class:`str`
            The source URL for the thumbnail. Only HTTP(S) is supported.
        """

        self.thumbnail = url
        return self

    @property
    def video(self) -> _EmbedVideoProxy:
        """Returns an ``EmbedProxy`` denoting the video contents.

        Possible attributes include:

        - ``url`` for the video URL.
        - ``height`` for the video height.
        - ``width`` for the video width.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, "_video", {}))  # type: ignore

    @property
    def provider(self) -> _EmbedProviderProxy:
        """Returns an ``EmbedProxy`` denoting the provider contents.

        The only attributes that might be accessed are ``name`` and ``url``.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, "_provider", {}))  # type: ignore

    @property
    def author(self) -> EmbedAuthor:
        """:class:`EmbedAuthor`: The author of the embed."""
        return getattr(self, "_author", EmbedAuthor())  # type: ignore

    @author.setter
    def author(self, author: MaybeEmpty[EmbedAuthor]):
        if author is EmptyEmbed:
            del self._author
            return

        if not isinstance(author, EmbedAuthor):
            raise TypeError(f"Expected EmbedAuthor received {author.__class__.__name__} instead")

        self._author = author

    @author.deleter
    def author(self) -> None:
        try:
            del self._author
        except AttributeError:
            pass

    def set_author(
        self: E, *, name: Any, url: MaybeEmpty[Any] = EmptyEmbed, icon_url: MaybeEmpty[Any] = EmptyEmbed
    ) -> E:
        """Sets the author for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        name: :class:`str`
            The name of the author.
        url: :class:`str`
            The URL for the author.
        icon_url: :class:`str`
            The URL of the author icon. Only HTTP(S) is supported.
        """

        fields = {
            "name": str(name),
        }

        if url is not EmptyEmbed:
            fields["url"] = str(url)

        if icon_url is not EmptyEmbed:
            fields["icon_url"] = str(icon_url)

        self.author = EmbedAuthor(**fields)
        return self

    def remove_author(self: E) -> E:
        """Clears embed's author information.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 1.4
        """
        del self.author
        return self

    @property
    def fields(self) -> List[EmbedField]:
        """List[:class:`EmbedField`]: A list of embed fields. This is an empty list if there are no fields."""
        return getattr(self, "_fields", [])

    @fields.setter
    def fields(self, fields: MaybeEmpty[Iterable[EmbedField]], /) -> None:
        """Replace or set the embed's fields.

        Parameters
        -----------
        fields: Iterable[:class:`EmbedField`]
            An iterable of fields to replace the current fields with.
            Passing an emptpy list or :attr:`Empty` will clear the fields.
        """
        if fields is EmptyEmbed or fields == []:
            self.clear_fields()
            return

        _fields: Iterable[EmbedField] = fields  # type: ignore
        if not all(isinstance(field, EmbedField) for field in _fields):
            raise TypeError("Expected an iterable of EmbedFields.")

        if len(list(_fields)) > 25:
            raise ValueError("maximum number of fields exceeded, max 25.")

        self._fields = list(_fields)

    @fields.deleter
    def fields(self) -> None:
        """ "Removes all fields from this embed."""
        try:
            del self._fields
        except AttributeError:
            pass

    def append_field(self, field: EmbedField, /):
        """Appends a :class:`EmbedField` to the embed.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        field: :class:`EmbedField`
            The field to append to the embed.
        """

        if not isinstance(field, EmbedField):
            raise TypeError(f"Expected EmbedField received {field.__class__.__name__} instead")

        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]

        return self

    def add_field(self: E, *, name: Any, value: Any, inline: bool = True) -> E:
        """Adds a field to the embed object.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        name: :class:`str`
            The name of the field.
        value: :class:`str`
            The value of the field.
        inline: :class:`bool`
            Whether the field should be displayed inline.
        """

        fields = {
            "inline": inline,
            "name": str(name),
            "value": str(value),
        }

        return self.append_field(EmbedField(**fields))

    def insert_field_at(self: E, index: int, *, name: Any, value: Any, inline: bool = True) -> E:
        """Inserts a field before a specified index to the embed.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 1.2

        Parameters
        -----------
        index: :class:`int`
            The index of where to insert the field.
        name: :class:`str`
            The name of the field.
        value: :class:`str`
            The value of the field.
        inline: :class:`bool`
            Whether the field should be displayed inline.
        """

        fields = {
            "inline": inline,
            "name": str(name),
            "value": str(value),
        }
        fields = EmbedField(**fields)
        try:
            self._fields.insert(index, fields)
        except AttributeError:
            self._fields = [fields]

        return self

    def clear_fields(self) -> None:
        """Removes all fields from this embed."""
        del self.fields

    def remove_field(self, index: int) -> None:
        """Removes a field at a specified index.

        If the index is invalid or out of bounds then the error is
        silently swallowed.

        .. note::

            When deleting a field by index, the index of the other fields
            shift to fill the gap just like a regular list.

        Parameters
        -----------
        index: :class:`int`
            The index of the field to remove.
        """
        try:
            del self._fields[index]
        except (AttributeError, IndexError):
            pass

    def set_field_at(self: E, index: int, *, name: Any = None, value: Any = None, inline: bool = True) -> E:
        """Modifies a field to the embed object.

        The index must point to a valid pre-existing field.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        index: :class:`int`
            The index of the field to modify.
        name: Optional[:class:`str`]
            The new name of the field.
            The previous name will be used if this is ``None`` (default).
        value: Optional[:class:`str`]
            The value of the field.
            The previous name will be used if this is ``None`` (default).
        inline: :class:`bool`
            Whether the field should be displayed inline. Defaults to ``True``.

        Raises
        -------
        IndexError
            An invalid index was provided.
        """
        try:
            field = self._fields[index]
        except (AttributeError, TypeError, IndexError):
            raise IndexError("field index out of range")

        if not name and not value and inline == field.inline:
            return self

        field._edit(
            name=str(name or field.name),
            value=str(value or field.value),
            inline=inline if inline != field.inline else field.inline,
        )

        return self

    def to_dict(self) -> EmbedData:
        """Converts this embed object into a dict."""
        result = {}

        for attr in ("footer", "author", "fields"):
            attr_value = getattr(self, f"_{attr}", None)
            if not attr_value or attr_value is EmptyEmbed:
                continue

            if attr == "fields":
                result[attr] = [field.to_dict() for field in attr_value]
            else:
                result[attr] = attr_value.to_dict()

        for image_attrs in ("image", "thumbnail"):
            image_value = getattr(self, f"_{image_attrs}", None)
            if not image_value:
                continue

            result[image_attrs] = image_value

        try:
            colour = result.pop("colour")
        except KeyError:
            pass
        else:
            if colour:
                result["color"] = colour.value

        try:
            timestamp = result.pop("timestamp")
        except KeyError:
            pass
        else:
            if timestamp:
                if timestamp.tzinfo:
                    result["timestamp"] = timestamp.astimezone(tz=datetime.timezone.utc).isoformat()
                else:
                    result["timestamp"] = timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()

        # add in the non raw attribute ones
        if self.type:
            result["type"] = self.type

        if self.description:
            result["description"] = self.description

        if self.url:
            result["url"] = self.url

        if self.title:
            result["title"] = self.title

        return result  # type: ignore
