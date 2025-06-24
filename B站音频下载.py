import requests
import json
import os
from urllib.parse import quote
import time

# 在此处填入你的Bilibili Cookie
cookie = "XXX"

def search_bilibili_videos(keyword, page=1, page_size=20):
    """搜索B站视频并返回结果列表"""
    search_url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={quote(keyword)}&page={page}&page_size={page_size}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
        "Cookie": cookie
    }
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        videos = []
        for item in data['data']['result']:
            if item['result_type'] == 'video':
                videos.extend(item['data'])
                break
        return videos
    except Exception as e:
        print(f"搜索失败: {e}")
        return []


def get_video_audio_url(bvid):
    """获取视频的音频流 URL"""
    # 获取 cid
    cid = get_video_cid(bvid)
    if not cid:
        return None

    # 调用 playurl 接口
    play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=0&fnval=16"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/{bvid}",
        "Cookie": cookie
    }
    try:
        response = requests.get(play_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data['code'] == 0:
            # 提取 DASH 格式中的音频流
            if 'dash' in data['data']:
                audio_info = data['data']['dash']['audio'][0]
                return audio_info['base_url']
            else:
                print("未找到 DASH 格式的音频流")
                return None
        else:
            print(f"获取音频流失败: {data['message']}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def get_video_cid(bvid):
    """通过 bvid 获取视频的 cid"""
    view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/{bvid}",
        "Cookie": cookie
    }
    try:
        response = requests.get(view_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data['code'] == 0:
            return data['data']['cid']  # 返回第一个分片的 cid
        else:
            print(f"获取 cid 失败: {data['message']}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def download_audio(url, title, output_dir="downloads"):
    """下载音频文件"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 过滤非法字符
    title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in [' ', '-', '_']]).rstrip()
    filename = f"{output_dir}/{title}.mp3"
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"下载成功: {filename}")
    except Exception as e:
        print(f"下载失败: {e}")


def main():
    keyword = input("请输入要搜索的标题关键字: ")
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取 100 个视频
    videos = []
    page = 1
    while len(videos) < 100:
        print(f"正在获取第 {page} 页数据...")
        new_videos = search_bilibili_videos(keyword, page=page, page_size=20)
        if not new_videos:
            break
        videos.extend(new_videos)
        page += 1
        time.sleep(1)  # 避免请求过快

    if not videos:
        print("未找到相关视频")
        return

    print(f"共找到 {len(videos)} 个视频，开始下载音频...")

    # 下载前 100 个视频的音频
    for i, video in enumerate(videos[:100]):
        try:
            print(f"正在处理第 {i + 1} 个视频: {video['title']}")
            bvid = video['bvid']
            audio_url = get_video_audio_url(bvid)
            if audio_url:
                download_audio(audio_url, video['title'], output_dir)
            else:
                print(f"未找到音频流: {video['title']}")
        except Exception as e:
            print(f"处理视频失败: {video['title']}, 错误: {e}")
        time.sleep(1)  # 避免请求过快

    print("音频下载完成！")


if __name__ == "__main__":
    main()
