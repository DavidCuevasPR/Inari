import math
from dataclasses import dataclass

import aiosqlite
import discord
from discord.ext import commands
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

from utils import numbered, pages


@dataclass
class UserCoords:
    user_id: int
    name: str
    base_coords: str
    guild_id: int


@dataclass
class AdminCoords:
    name: str
    coords: str
    creator_id: int
    guild_id: int


@dataclass
class Shop:
    user_id: int
    name: str
    items: str
    guild_id: int


async def shop_table_create():
    async with aiosqlite.connect("coorddata.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS shops (
                                user_id integer,
                                name text,
                                items text,
                                guild_id integer
                                );""")
        await db.commit()
    print('Shops table created or already existed')


async def admincoords_table_create():
    async with aiosqlite.connect("coorddata.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS admincoords (
                                name text,
                                coordinates text,
                                creator integer,
                                guild_id integer
                                );""")
        await db.commit()
    print('Admincoords table created or already existed')


async def coords_table_create():
    async with aiosqlite.connect("coorddata.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS coords (
                                        user_id integer,
                                        name text,
                                        base_coords text,
                                        guild_id integer
                                        );""")
        await db.commit()
    print('Coords table created or already existed')


async def calculate_distance(x1, z1, x2, z2):
    dist = math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)
    return round(dist)


class coordinates(commands.Cog):
    """Commands to create and store coordinates for your Minecraft server"""

    def __init__(self, bot):
        self.bot = bot
        self.usercoords = []
        self.admincoords = []
        self.shops = []
        bot.loop.create_task(self.startup())

    async def startup(self):
        async with aiosqlite.connect("coorddata.db") as db:
            await coords_table_create()
            await admincoords_table_create()
            await shop_table_create()
            await db.commit()

            async with db.execute("""SELECT * FROM coords""") as cursor:
                usercoord_rows = await cursor.fetchall()
                if usercoord_rows:
                    for coord_tup in usercoord_rows:
                        ucoord = UserCoords(
                            user_id=coord_tup[0],
                            name=coord_tup[1],
                            base_coords=coord_tup[2],
                            guild_id=coord_tup[3]
                        )
                        self.usercoords.append(ucoord)

            async with db.execute("""SELECT * FROM admincoords""") as cursor:
                admincoord_rows = await cursor.fetchall()
                if admincoord_rows:
                    for admin_tup in admincoord_rows:
                        adm_coord = AdminCoords(
                            name=admin_tup[0],
                            coords=admin_tup[1],
                            creator_id=admin_tup[2],
                            guild_id=admin_tup[3])
                        self.admincoords.append(adm_coord)

            async with db.execute("""SELECT * FROM shops""") as cursor:
                shop_rows = await cursor.fetchall()
                if shop_rows:
                    for shop_tup in shop_rows:
                        shop = Shop(user_id=shop_tup[0], name=shop_tup[1],
                                    items=shop_tup[2], guild_id=shop_tup[3])
                        self.shops.append(shop)

    @commands.command()
    async def convert(self, ctx: commands.Context, x: int, z: int):
        """
        Converts the entered x and z coords into overworld and nether coords
        **e.g**: `$convert <x> <z>`
        """
        await ctx.message.delete()
        nether_coords = f"{x * 8} / {z * 8}"
        overworld_coords = f"{x // 8} / {z // 8}"
        coords_emb = discord.Embed(title="Converted coords",
                                   colour=0xFFAE00,
                                   description="Coords are in format: x / z")
        coords_emb.add_field(name="Overworld to Nether",
                             value=f"{x} / {z} ---> {nether_coords}",
                             inline=False)
        coords_emb.add_field(name="Nether to Overworld",
                             value=f"{x} / {z} ---> {overworld_coords}",
                             inline=False)
        await ctx.send(embed=coords_emb)

    @commands.command(aliases=['cs'])
    async def coordset(self, ctx: commands.Context, x: int, z: int, y=62, name=''):
        """
        Sets the coord of the user using format and a name(base, spawner, etc)
        **e.g**: `$coordset <x> <z> <y> <name>`
        """
        await ctx.message.delete()
        ints = [x, z, y]
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        if y > 256 or y < 0:
            await ctx.send(embed=discord.Embed(
                title='Y level can\'t be higher than 256 blocks \n'
                      'Or lower than 0',
                colour=0xFF0000))
            return
        await confirmation.confirm(
            f"Are you sure you want to set your coords as:\n"
            f" x: {x}/ z: {z}/ y: {y}/ name: {name}?"
        )
        if confirmation.confirmed:
            str_of_coords = "/".join([str(i) for i in ints])
            async with aiosqlite.connect("coorddata.db") as db:
                await db.execute(
                    """INSERT INTO
                    coords(user_id, name, base_coords, guild_id)
                    VALUES (?,?,?,?)""",
                    (ctx.author.id, name, str_of_coords, ctx.guild.id,))
                await db.commit()

            ucoord = UserCoords(
                user_id=ctx.author.id,
                name=name,
                base_coords=str_of_coords,
                guild_id=ctx.guild.id)
            self.usercoords.append(ucoord)
            await confirmation.update(
                f"Coords set for {ctx.author.display_name}(Name: {name})"
                f"as {str_of_coords}"[:100],
                color=0xFFAE00)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command()
    async def coords(self, ctx: commands.Context, user: discord.Member = None):
        """
        Returns the coords of the user mentioned, if no user is mentioned, returns the author's coords
        **e.g**: `$coords <@user>`
        """
        await ctx.message.delete()
        if not user:
            user = ctx.author
        embed_nocrds = discord.Embed(
            title=f'No coords set for {user.display_name}', colour=0xFF0000)
        gen = [
            (ucoords.base_coords, ucoords.name)
            for ucoords in self.usercoords if ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id
        ]
        if not gen:
            await ctx.send(embed=embed_nocrds)
            return
        await (BotEmbedPaginator(ctx, pages(numbered(
            [f"Coords: {tup[0]} | Name: {tup[1]}"
             for tup in gen]
        ), n=10, title=f'Coordinates for {user.display_name}'))).run()

    @commands.command()
    async def nearme(self, ctx: commands.Context, x: int, z: int, distance: int = 100):
        """
        Returns the coords and name of people near your base
        **e.g**:`$nearme <x> <z> <distance>`
        __<distance> defaults to 100__
        """
        await ctx.message.delete()
        people_gen = [
            (ucrd.base_coords,)
            for ucrd in self.usercoords if ucrd.guild_id == ctx.guild.id and ucrd.user_id != ctx.author.id
        ]
        int_people_coords = []
        for tup in people_gen:
            int_people_coords.append(tuple(tup[0].split('/')))
        matched_coords = []
        for tup in int_people_coords:
            if await calculate_distance(x, z, int(tup[0]), int(tup[1])) <= distance:
                matched_coords.append(f'{tup[0]}/{tup[1]}/{tup[2]}')
        match_gen = [
            (ucoords.user_id, ucoords.base_coords, ucoords.name)
            for ucoords in self.usercoords if ucoords.guild_id == ctx.guild.id and ucoords.base_coords in matched_coords
        ]
        if not match_gen:
            await ctx.send(embed=discord.Embed(title='No coords found',
                                               colour=0xFF0000))
            return
        await (BotEmbedPaginator(ctx, pages(numbered(
            [f"User: {ctx.guild.get_member(tup[0]).display_name}\n"
             f"Coords: {tup[1]} | Name: {tup[2]}"
             for tup in match_gen]
        ), n=10, title=f"People near your coords {x}/{z}\nCoords are in format x/z/y"))).run()

    @commands.command()
    async def delcoord(self, ctx: commands.Context, user: discord.Member = None):
        """
        Deletes the coords that the user chooses from the multiple choice embed
        **ADMIN ONLY**:
        Do `delcoord <@user>` to delete shops for that user
        """
        await ctx.message.delete()
        if user:
            if ('administrator', True) not in ctx.author.guild_permissions:
                await ctx.send(embed=discord.Embed(title="You don't have the administrator permission!"))
                return
            confirmation = BotConfirmation(ctx, 0xFFAE00)
            delcoords_gen = [
                (ucoords.base_coords,)
                for ucoords in self.usercoords if ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id
            ]
            if not delcoords_gen:
                await ctx.send(embed=discord.Embed(title="This user doesn't have any registered coords",
                                                   colour=0xFF0000))
                return
            multiple_choice = BotMultipleChoice(ctx,
                                                [coords[0] for coords in delcoords_gen] + ['Delete all coords'],
                                                "Select the coordinates you wish to delete", colour=0xFFAE00)
            await multiple_choice.run()
            await multiple_choice.quit()
            async with aiosqlite.connect("coorddata.db") as db:
                if multiple_choice.choice == 'Delete all coords':
                    await confirmation.confirm("Are you sure you want to delete all coords for this user?")
                    if confirmation.confirmed:
                        await confirmation.update("Confirmed", color=0xFFAE00)
                        await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=?", (
                            ctx.guild.id, user.id))
                        await db.commit()
                        for ucoords in self.usercoords:
                            if ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id:
                                self.usercoords.remove(ucoords)
                        embed_delete = discord.Embed(
                            title=f"All of {user.display_name}'s coords deleted",
                            colour=0xFFAE00)
                        await ctx.send(embed=embed_delete)
                    else:
                        await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

                elif multiple_choice.choice:
                    await confirmation.confirm(f"Are you sure you want to delete {multiple_choice.choice}?")
                    if confirmation.confirmed:
                        await confirmation.update("Confirmed", color=0xFFAE00)
                        await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=? AND base_coords=?", (
                            ctx.guild.id, user.id, multiple_choice.choice))
                        await db.commit()
                        for ucoords in self.usercoords:
                            if (ucoords.base_coords == multiple_choice.choice
                                    and ucoords.user_id == user.id and ucoords.guild_id == ctx.guild.id):
                                self.usercoords.remove(ucoords)
                        embed_delete = discord.Embed(
                            title=f"{user.display_name}'s {multiple_choice.choice} coords deleted", colour=0xFFAE00)
                        await ctx.send(embed=embed_delete)
                    else:
                        await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)
        else:
            author_coords = [
                ucoords.base_coords
                for ucoords in self.usercoords if ucoords.user_id == ctx.author.id and ucoords.guild_id == ctx.guild.id
            ]
            if not author_coords:
                await ctx.send(embed=discord.Embed(title='You have no coords set!',
                                                   colour=0xFF0000))
                return
            multiple_choice = BotMultipleChoice(ctx, author_coords,
                                                "Select the coordinates you wish to delete", colour=0xFFAE00)
            await multiple_choice.run()
            await multiple_choice.quit()
            if multiple_choice.choice:
                confirmation = BotConfirmation(ctx, 0xFFAE00)
                await confirmation.confirm(f"Are you sure you want to delete {multiple_choice.choice}?")
                if confirmation.confirmed:
                    for ucoords in self.usercoords:
                        if (ucoords.base_coords == multiple_choice.choice
                                and ucoords.guild_id == ctx.guild.id and ucoords.user_id == ctx.author.id):
                            self.usercoords.remove(ucoords)
                    async with aiosqlite.connect("coorddata.db") as db:
                        await db.execute("DELETE FROM coords WHERE guild_id=? AND user_id=? AND base_coords=?", (
                            ctx.guild.id, ctx.author.id, multiple_choice.choice))
                        await db.commit()
                    await confirmation.update(f"Your coords({multiple_choice.choice}), have been deleted",
                                              color=0xFFAE00)
                else:
                    await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command()
    async def allcoords(self, ctx: commands.Context):
        """
        Returns a list of the coords from all users
        """
        await ctx.message.delete()
        embed_error = discord.Embed(title='No coords set', colour=0xFF0000)
        allcoords_gen = [
            (ucoords.user_id, ucoords.base_coords, ucoords.name)
            for ucoords in self.usercoords if ucoords.guild_id == ctx.guild.id
        ]
        if not allcoords_gen:
            await ctx.send(embed=embed_error)
            return
        await (BotEmbedPaginator(ctx, pages(numbered(
            [f"{ctx.guild.get_member(tup[0]).display_name}: {tup[1] + ' / ' + tup[2]}"
             for tup in allcoords_gen]
        ), n=10, title=f'Coordinates for {ctx.guild.name}'))).run()

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['setadmin'])
    async def setadmincoords(self, ctx: commands.Context, name: str, x: int, z: int, y=62):
        """
        **ADMIN ONLY**
        Sets a server coordinate(end portal, spawn, etc) by an admin
        If the name uses spaces wrap it in " "
        **e.g**: '$setadmincrds <name> <x> <z> <y>`
        __<y> defaults to 62 if not stated__
        """
        await ctx.message.delete()
        if y > 256 or y < 0:
            await ctx.send(embed=discord.Embed(title="Y level can't be higher than 256 blocks \n"
                                                     "Or lower than 0",
                                               colour=0xFF0000))
            return
        ints = [x, z, y]
        str_of_coords = "/".join([str(i) for i in ints])
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm(f"Are you sure you want to set the admin coords as:\n"
                                   f" {name} x: {x}/ z: {z}/ y:{y}?")
        if confirmation.confirmed:
            await confirmation.update(f'Admin coords for {name} set as\n'
                                      f'{str_of_coords} by {ctx.author.display_name}',
                                      color=0xFFAE00)
            async with aiosqlite.connect("coorddata.db") as db:
                await db.execute(
                    """INSERT INTO admincoords(name, coordinates, creator, guild_id) VALUES(?,?,?,?)""",
                    (name, str_of_coords, ctx.author.id, ctx.guild.id))
                await db.commit()
            adm_coords = AdminCoords(name=name, coords=str_of_coords,
                                     creator_id=ctx.author.id, guild_id=ctx.guild.id)
            self.admincoords.append(adm_coords)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command(aliases=['alladmin'])
    async def alladmincoords(self, ctx: commands.Context):
        """
        Returns all the admin coords of the current server
        """
        await ctx.message.delete()
        embed_error = discord.Embed(title='No admin coords set', colour=0xFF0000)
        alladm_gen = [
            (adm.name, adm.coords, adm.creator_id)
            for adm in self.admincoords if adm.guild_id == ctx.guild.id
        ]
        if not alladm_gen:
            await ctx.send(embed=embed_error)
            return
        else:
            await (BotEmbedPaginator(ctx, pages(
                numbered(
                    [f"{tup[0]}: {tup[1]} | Creator: {ctx.guild.get_member(tup[2]).display_name}"
                     for tup in alladm_gen]
                ), n=10, title=f'Admin coordinates for {ctx.guild.name}\n (name)(x)(z)(y)'))).run()

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['deladmin'])
    async def deleteadmincoords(self, ctx: commands.Context):
        """
        **ADMIN ONLY**
        Deletes the admin coords selected from the multiple choice
        """
        await ctx.message.delete()
        deladmin_gen = [
            (adm.name,)
            for adm in self.admincoords if adm.guild_id == ctx.guild.id
        ]
        async with aiosqlite.connect("coorddata.db") as db:
            multiple_choice = BotMultipleChoice(ctx, [tup[0] for tup in deladmin_gen],
                                                "Select the coords you wish to delete", colour=0xFFAE00)
            await multiple_choice.run()
            await multiple_choice.quit()
            confirmation = BotConfirmation(ctx, 0xFFAE00)
            if multiple_choice.choice:
                await confirmation.confirm("Are you sure?")
                if confirmation.confirmed:
                    for adm in self.admincoords:
                        if adm.name == multiple_choice.choice and adm.guild_id == ctx.guild.id:
                            self.admincoords.remove(adm)
                    await db.execute(
                        """DELETE FROM admincoords WHERE name=? AND guild_id=?""",
                        (multiple_choice.choice, ctx.guild.id,))
                    await db.commit()
                    embed_del = discord.Embed(
                        title=f'Admin coords for {multiple_choice.choice} deleted',
                        description=f'Deleted by {ctx.author.display_name}', colour=0xFF0000)
                    await ctx.send(embed=embed_del)
                else:
                    await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)

    @commands.command(aliases=['ss'])
    async def shopset(self, ctx: commands.Context, name: str, *items: str):
        """
        Sets a shop
        **e.g**: $shopset <name> <items it sells>
        __Wrap <name> in " "  if it uses spaces__
        """
        await ctx.message.delete()
        slash_sep_items = '/'.join(items)
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm(f"Are you sure you want to set your shop as:\n"
                                   f"Name: {name} / Sells: {slash_sep_items}")
        if confirmation.confirmed:
            shop = Shop(user_id=ctx.author.id, name=name, items=slash_sep_items, guild_id=ctx.guild.id)
            self.shops.append(shop)
            async with aiosqlite.connect("coorddata.db") as db:
                await db.execute("""INSERT INTO shops (user_id, name, items, guild_id) VALUES(?,?,?,?)""",
                                 (ctx.author.id, name, slash_sep_items, ctx.guild.id))
                await db.commit()
            await confirmation.update(f'Shop for {ctx.author.display_name} set as:'
                                      f'Name: {name} / Sells: {slash_sep_items}'[:100],
                                      color=0xFFAE00)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command()
    async def shops(self, ctx: commands.Context, user: discord.Member = None):
        """
        Let's you see the mentioned user's shops
        **e.g**: `$shops <@user>`
        """
        await ctx.message.delete()
        if not user:
            user = ctx.author
        shops_gen = [
            (shops.name, shops.items)
            for shops in self.shops if shops.user_id == user.id and shops.guild_id == ctx.guild.id
        ]
        if not shops_gen:
            await ctx.send(embed=discord.Embed(title=f"{user.display_name} doesn't own any shops",
                                               colour=0xFF0000))
            return
        await (BotEmbedPaginator(ctx, pages(numbered(
            [f"Name: {tup[0]}\nItems: {tup[1]}"
             for tup in shops_gen]
        ), n=10, title=f"Shops owned by {user.display_name}"))).run()

    @commands.command()
    async def delshop(self, ctx: commands.Context, user: discord.Member = None):
        """
        Deletes the shops that the user chooses from the multiple choice embed
        **ADMIN ONLY**:
        Do `$delshop <@user>` to delete shops for that user
        """
        await ctx.message.delete()
        if user:
            if ('administrator', True) not in ctx.author.guild_permissions:
                await ctx.send(embed=discord.Embed(title="You don't have the administrator permission!"))
                return
            delshops_gen = [
                shop.name
                for shop in self.usercoords if shop.user_id == user.id and shop.guild_id == ctx.guild.id
            ]
            if not delshops_gen:
                await ctx.send(embed=discord.Embed(title="This user doesn't have any registered shops",
                                                   colour=0xFF0000))
                return
            confirmation = BotConfirmation(ctx, 0xFFAE00)
            multiple_choice = BotMultipleChoice(
                ctx,
                delshops_gen + ['Delete all shops'],
                "Select the coordinates you wish to delete",
                colour=0xFFAE00
            )
            await multiple_choice.run()
            await multiple_choice.quit()
            async with aiosqlite.connect("coorddata.db") as db:
                if multiple_choice.choice == 'Delete all shops':
                    await confirmation.confirm("Are you sure you want to delete all shops for this user?")
                    if confirmation.confirmed:
                        await confirmation.update("Confirmed", color=0xFFAE00)
                        await db.execute("DELETE FROM shops WHERE guild_id=? AND user_id=?", (
                            ctx.guild.id, user.id))
                        await db.commit()
                        for shop in self.shops:
                            if shop.user_id == user.id and shop.guild_id == ctx.guild.id:
                                self.usercoords.remove(shop)
                        embed_delete = discord.Embed(
                            title=f"All of {user.display_name}'s shops deleted",
                            colour=0xFFAE00)
                        await ctx.send(embed=embed_delete)
                    else:
                        await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

                elif multiple_choice.choice:
                    await confirmation.confirm(f"Are you sure you want to delete {multiple_choice.choice}?")
                    if confirmation.confirmed:
                        await confirmation.update(f"{user.display_name}'s ({multiple_choice.choice}) shop deleted",
                                                  color=0xFFAE00)
                        await db.execute("DELETE FROM shops WHERE guild_id=? AND user_id=? AND name=?",
                                         (ctx.guild.id, user.id, multiple_choice.choice))
                        await db.commit()
                        for shop in self.shops:
                            if (shop.name == multiple_choice.choice
                                    and shop.user_id == user.id and shop.guild_id == ctx.guild.id):
                                self.usercoords.remove(shop)
                    else:
                        await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)
        else:
            author_shops = [
                shop.name
                for shop in self.shops if shop.user_id == ctx.author.id and shop.guild_id == ctx.guild.id
            ]
            if not author_shops:
                await ctx.send(embed=discord.Embed(title='You have no shops set!',
                                                   colour=0xFF0000))
                return
            multiple_choice = BotMultipleChoice(ctx, author_shops,
                                                "Select the shop you wish to delete",
                                                colour=0xFFAE00)
            await multiple_choice.run()
            await multiple_choice.quit()
            if multiple_choice.choice:
                confirmation = BotConfirmation(ctx, 0xFFAE00)
                await confirmation.confirm(f"Are you sure you want to delete {multiple_choice.choice}?")
                if confirmation.confirmed:
                    for shop in self.shops:
                        if (shop.name == multiple_choice.choice and shop.guild_id == ctx.guild.id
                                and shop.user_id == ctx.author.id):
                            self.shops.remove(shop)
                    async with aiosqlite.connect("coorddata.db") as db:
                        await db.execute("""DELETE FROM shops WHERE user_id=? AND name=? AND guild_id=?""",
                                         (ctx.author.id, multiple_choice.choice, ctx.guild.id))
                        await db.commit()
                        await confirmation.update(f"Your shop: ({multiple_choice.choice}) has been deleted",
                                                  color=0xFFAE00)
                else:
                    await confirmation.update("Not confirmed", hide_author=True, color=0xFF0000)

    @commands.command()
    async def allshops(self, ctx: commands.Context):
        """
        Shows all shops for the server
        """
        await ctx.message.delete()
        all_gen = [
            (shop.name, shop.items, shop.user_id)
            for shop in self.shops if shop.guild_id == ctx.guild.id
        ]
        if not all_gen:
            await ctx.send(embed=discord.Embed(title="No shops set",
                                               colour=0xFF0000))
            return
        await (BotEmbedPaginator(ctx, pages(numbered(
            [f"Name: {tup[0]} | Items: {tup[1]} | Owner: {ctx.guild.get_member(tup[2]).display_name}"
             for tup in all_gen]
        ), n=10, title=f'Coordinates for {ctx.guild.name}'))).run()


def setup(bot):
    bot.add_cog(coordinates(bot))
