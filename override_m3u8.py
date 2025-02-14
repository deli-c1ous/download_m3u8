import logging
import asyncio
import subprocess
from pathlib import Path

import m3u8
import aiohttp
from tqdm.asyncio import tqdm_asyncio


async def load_m3u8(s, m3u8_url):
    async with s.get(m3u8_url) as r: return m3u8.loads(await r.text(), uri=m3u8_url)


async def get_key(s, key_url):
    with open('key.bin', 'wb') as f:
        async with s.get(key_url) as r: f.write(await r.read())


async def fetch(s, index, segment):
    ts_name = f'{index}.ts'
    with open(f'ts_encrypt/{ts_name}', 'wb') as f:
        async with s.get(segment.absolute_uri) as r:
            async for chunk in r.content.iter_chunked(64 * 1024): f.write(chunk)


async def download_encrypt_ts(s, playlist):
    Path('ts_encrypt').mkdir(exist_ok=True)
    tasks = (fetch(s, index, segment) for index, segment in enumerate(playlist.segments))
    await tqdm_asyncio.gather(*tasks)


def new_m3u8(playlist):
    playlist.keys[0].uri = 'key.bin'
    for index, segment in enumerate(playlist.segments): segment.uri = f"ts_encrypt/{index}.ts"
    playlist.dump('new.m3u8')


def m3u82mp4(capture_output=True):
    subprocess.run([
        'ffmpeg',
        '-allowed_extensions', 'ALL',
        '-i', 'new.m3u8',
        '-c', 'copy',
        'output.mp4'
    ], check=True, capture_output=capture_output)


def clean_up():
    for ts_file in Path('ts_encrypt').iterdir(): ts_file.unlink()
    Path('ts_encrypt').rmdir()
    Path('new.m3u8').unlink()
    Path('key.bin').unlink()


async def main():
    connector = aiohttp.TCPConnector(limit=limit)
    async with aiohttp.ClientSession(connector=connector) as s:
        logging.info(f'正在读取m3u8链接：{m3u8_url}')
        playlist = await load_m3u8(s, m3u8_url)
        key = playlist.keys[0]
        logging.info(f'正在获取密钥key：{key.uri}')
        await get_key(s, key.uri)
        logging.info('正在下载ts文件')
        await download_encrypt_ts(s, playlist)
    logging.info('正在生成新的m3u8文件')
    new_m3u8(playlist)
    logging.info('正在转换新的m3u8文件为mp4文件')
    m3u82mp4()
    logging.info('正在清理临时文件')
    clean_up()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    limit = 30
    m3u8_url = ''
    asyncio.run(main())
