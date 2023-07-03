import logging
import os
import sys
from textwrap import dedent
from time import sleep

import requests
import telegram
from dotenv import load_dotenv


def main():
    load_dotenv()
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    telegram_chat_id = os.environ['TELEGRAM_CHAT_ID']
    devman_apikey = os.environ["DEVMAN_APIKEY"]
    logging.basicConfig(level=logging.INFO)

    dvmn_lp_url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_apikey}'}
    params = {}

    tg_bot = telegram.Bot(token=telegram_token)

    logging.info('Бот запущен.')
    while True:
        try:
            response = requests.get(dvmn_lp_url, headers=headers, params=params)
            response.raise_for_status()

            review_check_result = response.json()
            if review_check_result['status'] == 'timeout':
                params['timestamp'] = review_check_result['timestamp_to_request']
            elif review_check_result['status'] == 'found':
                params['timestamp'] = review_check_result['last_attempt_timestamp']

                if review_check_result['new_attempts'][0]['is_negative']:
                    message_text = f'''
                    Преподаватель проверил Вашу работу {review_check_result['new_attempts'][0]['lesson_title']}.
                    К сожалению, в работе нашлись ошибки.
                    Ссылка на урок: {review_check_result['new_attempts'][0]['lesson_url']}'''

                else:
                    message_text = f'''
                    Преподаватель проверил Вашу работу {review_check_result['new_attempts'][0]['lesson_title']}.
                    Работа принята!
                    Ссылка на урок: {review_check_result['new_attempts'][0]['lesson_url']}'''

                tg_bot.send_message(
                    text=dedent(message_text),
                    chat_id=telegram_chat_id,
                )
        except requests.exceptions.ReadTimeout:
            logging.info('Истекло время ожидания, повторный запрос...')
            continue

        except requests.ConnectionError:
            logging.info('Ошибка соединения, повторная попытка через 60 секунд.')
            sleep(60)
            continue

        except Exception:
            logging.warning('Непредвиденная ошибка!', exc_info=sys.exc_info())
            continue


if __name__ == '__main__':
    main()
