from datetime import datetime
from json import loads as json_loads
from logging import INFO, StreamHandler, basicConfig, error as log_error, getLogger, info as log_info
from os import environ, path as ospath
from time import sleep

from dotenv import load_dotenv
from pytz import timezone, utc
from requests import get as rget
from telegram import Bot
from telegram.ext import Updater, CallbackContext
from telegram.error import RetryAfter

basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', handlers=[StreamHandler()], level=INFO)

def getConfig(key):
    return environ.get(key, None)

CONFIG_ENV_URL = "https://gist.githubusercontent.com/DrtorrentX/a5170d53baede92cfd063ee59f2034d1/raw/.env" or None

if CONFIG_ENV_URL:
    try:
        res = rget(CONFIG_ENV_URL)
        if res.status_code == 200:
            log_info("Downloading .env")
            with open('.env', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download .env {res.status_code}")
    except Exception as e:
        log_error(f"CONFIG_ENV_URL: {e}")

CONFIG_JSON_URL = "https://gist.githubusercontent.com/DrtorrentX/660b68d2f139e17e79487cf99c2e59cb/raw/config.json" or None
if CONFIG_JSON_URL:
    try:
        res = rget(CONFIG_JSON_URL)
        if res.status_code == 200:
            log_info("Downloading config.json")
            with open('config.json', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download config.json {res.status_code}")
    except Exception as e:
        log_error(f"CONFIG_JSON_URL: {e}")

load_dotenv('.env', override=True)

LOGGER = getLogger(__name__)

BOT_TOKEN = "5171152924:AAGhbx29Y_6BBB6V13Csjif-HcRtxANzuMs" or None
if BOT_TOKEN is None:
    LOGGER.error('BOT_TOKEN is not set')
    exit(1)
if not ospath.exists('config.json'):
    LOGGER.error("Create config.json")
    exit(1)
try:
    config = json_loads(open('config.json', 'r').read())
    bots = config['bots']
    channels = config['channels']
except:
    LOGGER.error("Error: config.json is not valid")
    exit(1)
try:
    STATUS_UPDATE_INTERVAL = int(getConfig('STATUS_UPDATE_INTERVAL')) or 1800
except:
    STATUS_UPDATE_INTERVAL = 1800

TIME_ZONE = getConfig('TIME_ZONE') or 'Asia/Calcutta'

HEADER_MSG = getConfig('HEADER_MSG') or "🤖 <a href='https://telegram.dog/drtorrentxupdates'><b>Status</b></a> <b>Dr. Torrent X Bots</b> 🤖"

FOOTER_MSG = getConfig('FOOTER_MSG') or "🫂 Join: https://t.me/+B9ZF0UDMcM5mZjM9\n\n<b>⚒ Powered by</b> <a href='https://telegram.dog/drtorrentxupdates'>Dr. Torrent X Team ❤️</a>"

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


# ... (other imports and code)

updater = Updater(BOT_TOKEN, update_queue=None)

# Configure the request_kwargs with desired parameters
updater.bot._default_query_kwargs['timeout'] = 20
updater.bot._default_query_kwargs['connect_timeout'] = 15

# ... (rest of your code)


def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result


def get_readable_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except:
        return 'Error'


def editMessage(update_queue: CallbackContext, text: str, channel: dict):
    try:
        update_queue.bot.editMessageText(text=text, message_id=channel['message_id'], chat_id=channel['chat_id'],
                                         parse_mode='HTMl', disable_web_page_preview=True)
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return editMessage(update_queue, text, channel)
    except Exception as e:
        if 'chat not found' in str(e).lower():
            LOGGER.error(f"Bot not found in {channel['chat_id']}")
        elif 'message to edit not found' in str(e).lower():
            LOGGER.error(f"Message not found in {channel['chat_id']}")
        elif 'chat_write_forbidden' in str(e).lower():
            LOGGER.error(
                f"Chat_write_forbidden in {channel['chat_id']}")
        else:
            LOGGER.error(str(e))
        delete_channel(channel)


def delete_channel(channel):
    for k, v in channels.items():
        if v['chat_id'] == channel['chat_id']:
            LOGGER.info(f"Deleting channel {k}")
            del channels[k]
            del config['channels'][k]
            break


def footer():
    msg = f"\n{FOOTER_MSG}\n"
    msg += f"⏱ Update {datetime.now(utc).astimezone(timezone(TIME_ZONE)).strftime('%d/%m %H:%M:%S')} {TIME_ZONE}"
    return msg


def bot_status():
    s_msg = ''
    active_bots = 0
    allbots = bots.values()
    totalBotCount = len(allbots)
    for bot in allbots:
        try:
            resp = rget(f"{bot['base_url_of_bot']}/status")
            if resp.status_code == 200:
                resp = resp.json()
                s_msg += f'\n┌<b>Bot</b>: {bot["bot_uname"]} ✅\n'
                try:
                    s_msg += f'├<b>Commit Date</b>: {resp["commit_date"]}\n'
                except:
                    pass
                try:
                    s_msg += f'├<b>Bot Uptime</b>: {get_readable_time(resp["on_time"])}\n'
                except:
                    pass
                try:
                    s_msg += f'├<b>Alive</b>: {get_readable_time(resp["uptime"])}\n'
                except:
                    pass
                s_msg += f'├<b>Host</b>: {bot["host"]}\n'
                try:
                    s_msg += f'├<b>Up</b>: {get_readable_size(resp["network"]["sent"])} '
                    s_msg += f'| <b>DL</b>: {get_readable_size(resp["network"]["recv"])}\n'
                    s_msg += f'└<b>Free Disk</b>: {get_readable_size(resp["free_disk"])}/{get_readable_size(resp["total_disk"])}\n'
                except:
                    s_msg += '└<b>Something went wrong!</b>'
                active_bots += 1
            else:
                s_msg += f'\n┌<b>Bot</b>: {bot["bot_uname"]} ❌\n'
                s_msg += f'└<b>Host</b>: {bot["host"]}\n'
        except:
            try:
                LOGGER.error(f'Error: {bot["bot_uname"]}')
                s_msg += f'\n┌<b>Bot</b>: {bot["bot_uname"]} ❌\n'
                s_msg += f'└<b>Host</b>: {bot["host"]}\n'
            except:
                LOGGER.error('Error: json file is not valid')
            continue
    return s_msg, active_bots, totalBotCount


def edit_bot_status(update_queue: CallbackContext):
    s_msg, active_bots, allbots = bot_status()
    msg = f'\n🧲 <b>Available Bots</b>: {active_bots}/{allbots} \n'
    msg += s_msg
    update_queue.bot.send_message(chat_id=update_queue.job.context['chat_id'], text=msg)


def main(update_queue: CallbackContext):
    _channels = channels.values()
    if len(_channels) == 0:
        LOGGER.warning("No channels found")
        exit(1)
    msg = f"{HEADER_MSG}\n"+"{}"+f"{footer()}"
    status = edit_bot_status(update_queue)
    try:
        for channel in _channels:
            LOGGER.info(f"Updating {channel['chat_id']}: {channel['message_id']}")
            sleep(0.5)
            editMessage(update_queue, msg.format("<code>Updating...</code>"), channel)
            _status = msg.format(status)
            sleep(0.5)
            if len(_status.encode()) < 4000:
                editMessage(update_queue, _status, channel)
            else:
                LOGGER.warning(f"Message too long for {channel['chat_id']}")
    except Exception as e:
        LOGGER.error(f"Error: {e}")

def job_callback(update_queue: CallbackContext):
    main(update_queue)
    update_queue.job.context['job_queue'].run_once(job_callback, STATUS_UPDATE_INTERVAL)

if __name__ == '__main__':
    LOGGER.info("Starting...")
    job_queue = updater.job_queue
    job_queue.run_once(job_callback, 0)
    updater.start_polling()
    updater.idle()
