from typing import List, Any, Union

import aiosqlite
import discord


def pages(lst: List[Any],
          n: int, title: str, *, fmt: str = "```%s```", sep: str = "\n") -> List[discord.Embed]:
    # noinspection GrazieInspection
    """
        Paginates a list into embeds to use with :class:disputils.BotEmbedPaginator
        :param lst: the list to paginate
        :param n: the number of elements per page
        :param title: the title of the embed
        :param fmt: a % string used to format the resulting page
        :param sep: the string to join the list elements with
        :return: a list of embeds
        """
    l: List[List[str]] = group_list([str(i) for i in lst], n)
    pgs = [sep.join(page) for page in l]
    return [
        discord.Embed(
            title=f"{title} - {i + 1}/{len(pgs)}",
            description=fmt % pg
        ) for i, pg in enumerate(pgs)
    ]


def group_list(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Splits a list into sub-lists of n
    :param lst: the list
    :param n: the subgroup size
    :return: The list of lists
    """
    return [lst[i * n:(i + 1) * n] for i in range((len(lst) + n - 1) // n)]


def numbered(lst: List[Any]) -> List[str]:
    """
    Returns a numbered version of a list
    """
    return [f"{i} - {a}" for i, a in enumerate(lst)]
