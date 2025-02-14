import logging
import asyncio
import subprocess
from pathlib import Path

import m3u8
import aiohttp
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from tqdm.asyncio import tqdm_asyncio


async def load_m3u8(s, m3u8_url):
    async with s.get(m3u8_url) as r: return m3u8.loads(await r.text(), uri=m3u8_url)


async def get_key(s, key_url):
    async with s.get(key_url) as r: return await r.read()


async def fetch(s, index, segment, aes):
    ts_name = f'{index}.ts'
    with open(f'ts_decrypt/{ts_name}', 'wb') as f:
        async with s.get(segment.absolute_uri) as r:
            data = await r.read()
            data = unpad(aes.decrypt(data), AES.block_size)
            f.write(data)


async def download_decrypt_ts(s, playlist, aes):
    Path('ts_decrypt').mkdir(exist_ok=True)
    tasks = (fetch(s, index, segment, aes) for index, segment in enumerate(playlist.segments))
    await tqdm_asyncio.gather(*tasks)


def merge_tsfiles(ts_dir, merged_filename):
    with open(merged_filename, 'wb') as f1:
        for tsfile in sorted(Path(ts_dir).iterdir(), key=lambda x: int(x.stem)):
            with open(tsfile, 'rb') as f2: f1.write(f2.read())


def ts2mp4(capture_output=True):
    subprocess.run([
        'ffmpeg',
        '-i', 'merged.ts',
        '-c', 'copy',
        'merged.mp4'
    ], capture_output=capture_output, check=True)


def clean_up():
    for ts_file in Path('ts_decrypt').iterdir(): ts_file.unlink()
    Path('ts_decrypt').rmdir()
    Path('merged.ts').unlink()


async def main():
    connector = aiohttp.TCPConnector(limit=limit)
    async with aiohttp.ClientSession(connector=connector) as s:
        logging.info(f'正在读取m3u8链接：{m3u8_url}')
        playlist = await load_m3u8(s, m3u8_url)
        key = playlist.keys[0]
        logging.info(f'正在获取密钥key：{key.uri}')
        aes_key = await get_key(s, key.uri)
        iv = bytes.fromhex(key.iv[2:])
        aes = AES.new(key=aes_key, mode=AES.MODE_CBC, iv=iv)
        logging.info('正在下载ts文件')
        await download_decrypt_ts(s, playlist, aes)
    logging.info('正在合并ts文件')
    merge_tsfiles('ts_decrypt', 'merged.ts')
    logging.info('正在转换合并后的ts文件为mp4文件')
    ts2mp4()
    logging.info('正在清理临时文件')
    clean_up()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    limit = 30
    m3u8_url = ''
    asyncio.run(main())
