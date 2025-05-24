from elasticsearch import AsyncElasticsearch
import asyncio

es = AsyncElasticsearch(
    hosts=['http://localhost:9200'],  # 必须带 http://
    basic_auth=('elastic',),
    verify_certs=False,
    request_timeout=180               # timeout 改名为 request_timeout
)
async def main():
    # 检查连接
    if await es.ping():
        print("连接成功")
        print(await es.info())
    else:
        print("连接失败")

asyncio.run(main())