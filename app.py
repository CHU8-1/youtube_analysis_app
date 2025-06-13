import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 讀取機密資訊
api_key = st.secrets["youtube"]["api_key"]
channel_id = st.secrets["youtube"]["channel_id"]

# 設定頁面
st.set_page_config(page_title="YouTube 頻道影片分析", layout="wide")
st.title("📊 YouTube 頻道影片成效分析")

# 取得影片清單
@st.cache_data
def get_video_data(api_key, channel_id, max_results=50):
    # 1. 取得 Uploads 播放清單ID
    url_channel = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={api_key}"
    res_channel = requests.get(url_channel).json()
    uploads_id = res_channel['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # 2. 取得影片清單
    url_playlist = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_id}&maxResults={max_results}&key={api_key}"
    res_playlist = requests.get(url_playlist).json()

    videos = []
    for item in res_playlist["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        published_at = item["snippet"]["publishedAt"]
        videos.append({
            "video_id": video_id,
            "title": title,
            "published_at": published_at
        })

    return videos

# 取得影片統計資料
def get_video_stats(video_ids, api_key):
    stats = []
    for i in range(0, len(video_ids), 50):  # 分批最多50個
        ids_chunk = ",".join(video_ids[i:i+50])
        url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={ids_chunk}&key={api_key}"
        res = requests.get(url).json()
        for item in res["items"]:
            stats.append({
                "video_id": item["id"],
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "comments": int(item["statistics"].get("commentCount", 0))
            })
    return stats

# 主要流程
videos = get_video_data(api_key, channel_id)
video_ids = [v["video_id"] for v in videos]
stats = get_video_stats(video_ids, api_key)

# 合併資料
df_info = pd.DataFrame(videos)
df_stats = pd.DataFrame(stats)
df = pd.merge(df_info, df_stats, on="video_id")
df["published_at"] = pd.to_datetime(df["published_at"])

# 顯示資料
st.dataframe(df.sort_values(by="views", ascending=False))

# 畫圖：觀看數前10名
top_videos = df.sort_values(by="views", ascending=False).head(10)
fig = px.bar(top_videos, x="title", y="views", title="觀看數 Top 10", labels={"views": "觀看數", "title": "影片標題"})
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)
