import discord
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
import asyncio
from discord.ext import commands
import aiosqlite
from utils import pages, group_list, numbered


class coordinates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coordset(self, ctx, x: int, y: int, z: int):
        author_id = ctx.author.id
        author_nick = ctx.author
        authornick = author_nick.display_name
        guild = ctx.guild.id
        sql_create_coords_table = """CREATE TABLE IF NOT EXISTS coords (
                                                                 user_id integer,
                                                                 usernick text, 
                                                                 base_coords text,
                                                                 guild_id integer
                                                                 );"""
        ints = [x, y, z]
        string_coords = [str(int) for int in ints]
        str_of_coords = "/".join(string_coords)
        async with aiosqlite.connect("coorddata") as db:
            await db.execute(sql_create_coords_table)
            await db.execute("""INSERT INTO coords(user_id, usernick, base_coords, guild_id) VALUES (?,?,?,?)""",
                             (author_id, authornick, str_of_coords, guild,))
            await db.commit()
        await ctx.send('Coords set')

    @commands.command()
    async def coords(self, ctx, user: discord.Member):
        guild_id = ctx.guild.id
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute("SELECT * FROM coords WHERE guild_id=? and user_id=?",
                                  (guild_id, user.id,)) as cursor:
                rows = await cursor.fetchall()
        coords_list = f"{user.display_name}'s coords:\n"
        for i in rows:
            coords_list += f"{i[1]}\n"
        embed_coords = discord.Embed(title=f"{coords_list}", colour=0x00FF00)
        await ctx.send(embed=embed_coords)

    @commands.command()
    async def coordel(self, ctx):
        author_id = ctx.author.id
        author_nick = ctx.author
        guild_id = ctx.guild.id
        confirmation = BotConfirmation(ctx, 0x00FF00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            await confirmation.update("Confirmed", color=0x00FF00)
            async with aiosqlite.connect("coorddata") as db:
                await db.execute("DELETE FROM coords WHERE guild_id=? and user_id=?", (guild_id, author_id,))
                await db.commit()
            embed_delete = discord.Embed(title=f"{author_nick.display_name}'s coords deleted", colour=0x00FF00)
            await ctx.send(embed=embed_delete)
            await asyncio.sleep(1)
            await ctx.send('Now you live nowhere dummy :b')

        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)

    @commands.command()
    async def allcoords(self, ctx):
        author_id = ctx.author.id
        author_nick = ctx.author
        guild_id = ctx.guild.id
        guild = ctx.guild
        embed_error = discord.Embed(title='No coords set', colour=0xFF0000)
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute(
                    "SELECT usernick, base_coords FROM coords WHERE guild_id=?", (guild_id,)) as cursor:
                rows = await cursor.fetchall()
                if rows is None:
                    await ctx.send(embed=embed_error)
                coords = rows
                if (guild_id,) not in rows:
                    await ctx.send(embed=embed_error)
                else:
                    await (BotEmbedPaginator(ctx, pages(
                        numbered(coords), n=5, title=f'Coordinates for {guild}'))).run()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def delcoords(self, ctx, user: discord.Member):
        author_nick = ctx.author
        guild_id = ctx.guild.id
        confirmation = BotConfirmation(ctx, 0x00FF00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            await confirmation.update("Confirmed", color=0x00FF00)
            async with aiosqlite.connect("coorddata") as db:
                await db.execute("DELETE FROM coords WHERE guild_id=? and user_id=?", (guild_id, user.id,))
                await db.commit()
            embed_delete = discord.Embed(
                title=f"{author_nick.display_name}'s coords deleted",
                description=f'Coords deleted by {author_nick} ', colour=0x00FF00)
            await ctx.send(embed=embed_delete)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)


def setup(bot):
    bot.add_cog(coordinates(bot))
