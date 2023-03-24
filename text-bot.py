import os
from dotenv import load_dotenv
import discord
from utils.utils import bosses_dict, Boss 
from utils import load_bosses, set_channel
import asyncio
from datetime import datetime as dt
import sys

load_dotenv()
TOKEN = sys.argv[1]
CHANNEL = sys.argv[2]

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

bosses = dict() # global mutable state
channel = None
info = ''

@client.event
async def on_message(message):
    global bosses
    global info
    if message.author == client.user:
        return
    
    channel = message.channel
    if channel.name != CHANNEL:
        return

    text = message.content
    if text.startswith('-'):
        parts = text[1:].split()
        if len(parts) == 1:
            boss_name = parts[0].lower()
            if boss_name in bosses_dict.keys():
                del bosses[boss_name]
                await boss_untagged(channel, boss_name)
            else: 
                await command_not_found(channel)
        else:
            await command_not_found(channel)
    elif text.startswith('+'):
        parts = text[1:].split()
        if len(parts) == 1:
            boss_name = parts[0].lower()
            if boss_name in bosses_dict.keys():
                boss = bosses_dict.get(boss_name)
                boss.calc_respawn_time()
                bosses[boss.name]=boss
                export_all()
                await boss_tagged(channel, boss)
            else: 
                await command_not_found(channel)
        elif len(parts) == 3: # +breka 2022-01-29 05:10:10
            boss = Boss.from_export_str(text, is_manual=True)
            bosses[boss.name]=boss
            export_all()
            await boss_tagged(channel, boss)
        else:
            await command_not_found(channel)
    elif text == '!':
        if len(bosses.values()) > 0:
            # Messages in Discord should be not more than 2000 characters long.
            mard_msg = info + "\n" if info else ''
            all_bosses_str = [boss.boss_status_str() for boss in sorted(bosses.values())]
            len_bosses = len(all_bosses_str)
            first_msg = "\n".join(all_bosses_str[:len_bosses//2])
            second_msg = "\n".join(all_bosses_str[len_bosses//2:])
            await channel.send(mard_msg + first_msg)
            await channel.send(second_msg)
        else:
            await channel.send("@here \n no hay bosses.")
    elif text.lower().startswith('!info'):
        info = ", ".join(text[5:].strip().split(","))
        await channel.send("Información")
    elif text == '!restart':
        bosses.clear()
        await channel.send(f"Bosses eliminados")
    elif text == '!export': 
        await channel.send(export_msg())
    elif text == '!export_file': 
        export_all()
        await channel.send(f"BBDD exportada.")
    elif text == '!import_file':
        bosses = load_bosses()
        await channel.send(f"BBDD importada.")
    elif text == '?':
        await all_bosses_short(channel)
    elif text == '?help':
        await command_not_found(channel)
    else:
        pass

def export_msg() -> str:
    return "\n".join([boss.export_msg() for boss in sorted(bosses.values())])

def export_all():
    with open("assets/data/database",'w',encoding = 'utf-8') as file:
        file.write(export_msg())
    
async def boss_tagged(channel, boss):
    await channel.send(boss.boss_tagged_str())

async def boss_untagged(channel, boss_name):
    await channel.send(f"Boss **{boss_name}** eliminado de la lista.")

async def check_5m_for_text_notification(channel):
    if len(bosses.values()) > 0:
        sorted_bosses = sorted(bosses.values())
        soon_bosses = []
        delete_bosses = []
        for boss in sorted_bosses:
            (hours, minutes, seconds, is_valid) = boss.last_time()
            if not is_valid:
                delete_bosses.append(boss)
            elif is_valid and hours == 0 and minutes == 5 and seconds == 0:
                soon_bosses.append(boss)
            elif is_valid and hours == 0 and minutes == 1 and seconds == 1:
                soon_bosses.append(boss)
            elif is_valid and hours == 0 and minutes == 0 and seconds == 1:
                soon_bosses.append(boss)
            else:
                pass
                
        
        result_msg = ''
        if len(delete_bosses)>0:
            deleted_header = "@here\nBoss sin marcar:\n"
            msg = "\n".join([boss.not_tagged() for boss in delete_bosses])
            result_msg = result_msg + '\n' + deleted_header + msg + '\n'
            for boss in delete_bosses:
                boss = bosses_dict.get(boss.name)
                boss.calc_respawn_time()
                bosses[boss.name]=boss
                export_all()

        if (len(soon_bosses)>0):
            closed_header = "@here\nPróximo boss en 5 minutos:\n"
            msg = "\n".join([boss.boss_status_str() for boss in soon_bosses])
            result_msg = result_msg + closed_header + msg

        if result_msg:
            await channel.send(result_msg)
        

async def all_bosses_short(channel):
    msg = ", ".join([boss.boss_short_str() for boss in bosses_dict.values()])
    await channel.send(msg)

async def command_not_found(channel):
    header = "**Comandos disponibles:**"
    show_all = "**!** (Listado de bosses)"
    reset_all = "**!restart** (Borra todos los jefes)"
    import_all = "**!import_file** (Elimina todos y carga desde la base de datos, es necesario después de reiniciar el bot)"
    boss_names = "**?** (Lista de nombres de jefes)"
    add_boss = "**+breka** (Agrega el boss matado ahora)"
    add_boss_with_time = "**+breka 2022-02-03 05:53:00** (Agrega el boss, matado en la fecha y hora indicada)"
    delete_boss = "**-breka** (Elimina boss del listado)"
    help_msg = "**?help** - este listado de ayuda"
    boss_names = "**?** - Muestra los nombres de los jefes"
    info_msg = "**!info Bosses Dion: cruma3, breka, медуза** (establece información adicional)" 
    msg = "\n".join([header,show_all,reset_all,import_all,add_boss,add_boss_with_time,delete_boss,help_msg,boss_names,info_msg])
    await channel.send(msg)

async def text_notification():
    await client.wait_until_ready()
    channel = set_channel(client, sys.argv[2])
    while not client.is_closed():
        await check_5m_for_text_notification(channel)
        await asyncio.sleep(1) # task runs every 1 seconds

client.loop.create_task(text_notification())
client.run(TOKEN)

# python text-bot.py TOKEN CHANNEL
