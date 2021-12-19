import requests
import random
import discord
import os
from dotenv import load_dotenv
import mysql.connector


load_dotenv()
ID = os.getenv('ID')
KEY = os.getenv('KEY')
host = os.getenv('host')
user = os.getenv('user')
passwd = os.getenv('passwd')
database = os.getenv('database')
recipe_dict = dict()


db = mysql.connector.connect(
    host=host,
    user=user,
    passwd=passwd,
    database=database
)

mycursor = db.cursor()


def get_items(query):
    try:
        response = requests.get(
            "https://api.edamam.com/search?q={}&app_id={}&app_key={}".format(
                query, ID, KEY)
        )
        if response.status_code == 200:
            recipejson = response.json()
            if len(recipejson["hits"]) < 5:
                start = 0
                end = len(recipejson["hits"])
            else:
                start = random.randrange(0, len(recipejson["hits"]) - 5)
                end = start + 5
            for i in range(start, end):
                recipe_dict[recipejson['hits'][i]['recipe']['label']
                            ] = recipejson['hits'][i]['recipe']['shareAs']
            return recipe_dict
    finally:
        return recipe_dict


TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        if message.content.split()[0].lower() == "-recipe":
            if len(message.content.split()) == 1:
                return
            keyword = message.content.split(' ', 1)[1]
            recipes = get_items(keyword)
            mycursor.execute(
                "INSERT INTO TopSearches (keyword) VALUES(%s)", (keyword,))
            db.commit()

        elif message.content.split()[0].lower() == "-topsearches":
            mycursor.execute(
                "SELECT keyword, COUNT(keyword) AS fooCount FROM TopSearches GROUP BY keyword ORDER BY fooCount DESC LIMIT 5")
            embed = discord.Embed(
                title="Top Recipe Searches",
                description="Here are the top recipes",
                color=discord.Color.blue())
            embed.set_thumbnail(url="https://i.imgur.com/axLm3p6.jpeg")
            for x in mycursor:
                msg = "**%s** searched %s times" % (x[0], x[1])
                embed.add_field(name=msg, value="\u200b", inline=False)
            embed.set_footer(text="Try Another Recipe!")
            await message.channel.send(embed=embed)
            return
        else:
            return

        embed = discord.Embed(
            title="List of Recipes for {}".format(
                message.content.split(' ', 1)[1]),
            description="Here are some recipes",
            color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/axLm3p6.jpeg")
        for key, value in recipes.items():
            embed.add_field(name="**{}**".format(key),
                            value="{}".format(value), inline=False)
        embed.set_footer(text="Try Another Recipe!")
        await message.channel.send(embed=embed)
        recipes.clear()
    except Exception as e:
        print(e)
        return

client.run(TOKEN)
