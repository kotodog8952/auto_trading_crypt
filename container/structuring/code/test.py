import asyncio
import aiohttp
import time

async def fetch_url(url):
    start = time.time()
    print(f"[{start:.2f}] 開始: {url} のデータ取得")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text()
    
    # データに対する処理（ここではデータの長さを計算）
    process_start = time.time()
    length = len(data)
    process_end = time.time()
    print(f"データ処理完了: {url}, データの長さ: {length}, 処理時間: {process_end - process_start:.2f}秒")

    end = time.time()
    print(f"[{end:.2f}] 終了: {url} のデータ取得, 所要時間: {end - start:.2f}秒")
    return data

async def main():
    urls = ['https://example.com', 'https://www.google.com', 'https://www.python.org']
    tasks = [fetch_url(url) for url in urls]

    start_time = time.time()
    print(f"[{start_time:.2f}] 非同期タスクを開始します。")

    responses = await asyncio.gather(*tasks)

    end_time = time.time()
    print(f"[{end_time:.2f}] すべてのタスクが完了しました。全体の所要時間: {end_time - start_time:.2f}秒")

    for url, content in zip(urls, responses):
        print(f'URL: {url}, コンテンツの長さ: {len(content)}')

if __name__ == "__main__":
    asyncio.run(main())

