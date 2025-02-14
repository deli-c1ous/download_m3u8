# download_m3u8
download m3u8 videos using python
## Requirement
ffmpeg (with environment variables configured)
`pip install m3u8 pycryptodomex tqdm aiohttp`
## Introduction
`merge_ts.py`: async download ts files and decrypt it using pycryptodomex library, then use ffmpeg merge them into a mp4 file.
`override_m3u8.py`: async download ts files but not decrypt it, generate a new m3u8 file using m3u8 library with ts files' links being local file system paths, finally use ffmpeg to convert the new m3u8 file to a mp4 file.
Both methods work equally well.
