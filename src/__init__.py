import os
import asyncio
from shutil import copy
from aiohttp import web, WSMsgType

from .message import parse_message, create_message, BadMessage
from .process_handler import ProcessHandler, InvalidOperation

work_dir = os.environ.get("FURTHER_LINK_WORK_DIR", "/tmp")
lib = os.path.dirname(os.path.realpath(__file__)) + '/lib'
for file_name in os.listdir(lib):
    file = os.path.join(lib, file_name)
    if os.path.isfile(os.path.join(lib, file)):
        copy(file, work_dir)


async def status(request):
    return web.Response(text='OK')


async def handle_message(message, process_handler):
    m_type, m_data = parse_message(message)

    if (m_type == 'start'
            and 'sourceScript' in m_data
            and isinstance(m_data.get('sourceScript'), str)):
        await process_handler.start(m_data['sourceScript'])

    elif (m_type == 'stdin'
          and 'input' in m_data
          and isinstance(m_data.get('input'), str)):
        await process_handler.send_input(m_data['input'])

    elif (m_type == 'stop'):
        process_handler.stop()

    else:
        raise BadMessage()


async def exep(request):
    socket = web.WebSocketResponse()
    await socket.prepare(request)

    async def on_start():
        try:
            await socket.send_str(create_message('started'))
        except Exception as e:
            print(e)
        print('Started', process_handler.id)

    async def on_stop(exit_code):
        try:
            await socket.send_str(create_message('stopped', {'exitCode': exit_code}))
        except Exception as e:
            print(e)
        print('Stopped', process_handler.id)

    async def on_output(channel, output):
        try:
            await socket.send_str(create_message(channel, {'output': output}))
        except Exception as e:
            print(e)

    process_handler = ProcessHandler(
        on_start=on_start,
        on_stop=on_stop,
        on_output=on_output,
        work_dir=work_dir
    )
    print('New connection', process_handler.id)

    try:
        async for message in socket:
            print('Message', message)
            try:
                await handle_message(message.data, process_handler)
            except (BadMessage, InvalidOperation):
                await socket.send_str(
                    create_message('error', {'message': 'Bad message'})
                )
            print('Handled')
    except asyncio.CancelledError:
        print(f"the websocket({socket}) cancelled")
    except Exception as e:
        print('e', e)
    finally:
        print('f')
        await socket.close()

    print('Closed connection', process_handler.id)
    if process_handler.is_running():
        process_handler.stop()
    return socket
