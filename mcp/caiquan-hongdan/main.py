from typing import Any
import httpx,json,os,sys
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import asyncio

from datetime import datetime,timedelta
import random,hashlib
import math


mcp = FastMCP("caiquan-hongdan")

SPORTS_AIPHOST                          = 'https://sports-api-prod.ic6.co'
SPORTS_ACCOUNT_ID                       = os.getenv('SPORTS_ACCOUNT_ID') or ''
SPORTS_SECRET_KEY                       = os.getenv('SPORTS_SECRET_KEY') or ''

async def request_post(url,data={},headers={}):
    async with httpx.AsyncClient() as client:
        response                        = await client.post(url, json=data, headers=headers,timeout=180)
        if response.status_code != 200:
            raise Exception(f'获取失败:http status:{response.status_code}\n{json.dumps(data)}')
        content_type                    = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        else:
            return response.text


def to_sign(data):
    timestamp                           = str(int(datetime.now().timestamp()))
    randstr                             = str(random.randint(100000, 999999))
    sign                                = [
        f'timestamp={timestamp}',
        f'randstr={randstr}',
    ]
    for key,val in data.items():
        if isinstance(val,(dict)) == False and bool(val) == True:
            sign.append(f'{key}={val}')
    sign.sort()
    sign                                = '&'.join(sign) + SPORTS_SECRET_KEY
    md5_hash                            = hashlib.md5()
    md5_hash.update(sign.encode('utf-8'))
    sign                                = md5_hash.hexdigest()
    return { 'sign':sign, 'timestamp':timestamp, 'randstr':randstr, 'accountid': SPORTS_ACCOUNT_ID }

async def foot_match_list(params):
    now                                 = datetime.now()
    post                                = {
        "size"                          : 2000,
        "page"                          : 1,
        "match_status"                  : 1,
        "start_date"                    : now.strftime('%Y-%m-%d'),
        "end_date"                      : now.strftime('%Y-%m-%d'),
    }
    post.update(params)
    headers                             = {
        'Content-Type'                  : 'application/json'
    }
    headers.update(to_sign(post))
    data                                = await request_post(
        f"{SPORTS_AIPHOST}/api/foot_match/list",
        data                            = post,
        headers                         = headers,
    )
    if data['code'] !=1 :
        # await log(f'foot_match_list error: {data["msg"]}')
        return {"list":[],"count":0}
    return data['data']

async def foot_match_analysis(match_id):
    post                                = {'match_id':match_id}
    headers                             = {
        'Content-Type'                  : 'application/json'
    }
    headers.update(to_sign(post))
    data                                = await request_post(
        f"{SPORTS_AIPHOST}/api/foot_match/analysis",
        data                            = post,
        headers                         = headers,
    )
    if data['code'] !=1 :
        # await log(f'foot_match_analysis error: {data["msg"]}')
        return False
    return data['data']

async def foot_odds_history(match_id):
    post                                = { 'match_id':match_id }
    headers                             = {
        'Content-Type'                  : 'application/json'
    }
    headers.update(to_sign(post))
    data                                = await request_post(
        f"{SPORTS_AIPHOST}/api/foot_odds/history",
        data                            = post,
        headers                         = headers,
    )
    if data['code'] !=1 :
        # await log(f'foot_odds_history error: {data["msg"]}')
        return False
    if isinstance(data['data'],dict) == False:
        return False
    return data['data']

async def foot_match_type_rank(type_id):
    post                                = { 'type_id':type_id }
    headers                             = {
        'Content-Type'                  : 'application/json'
    }
    headers.update(to_sign(post))
    data                                = await request_post(
        f"{SPORTS_AIPHOST}/api/foot_match_type/rank_score",
        data                            = post,
        headers                         = headers,
    )
    if data['code'] !=1 :
        # await log(f'foot_match_type_rank error: {data["msg"]}')
        return False
    return data['data']

def filter_match(match,lottery):
    nowrrrow                            = datetime.now()
    # 不要超过2天的比赛
    if match['foot_match_buy_date'] > (nowrrrow + timedelta(days=1)).strftime('%Y-%m-%d'):
        return False
    # 不要已停售的比赛
    if match[f'foot_match_{lottery}_buy_end_time'] <= (nowrrrow+timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'):
        return False
    return True

def getWeek(time_string,prefix=None):
    date_object                         = datetime.strptime(time_string[:10], "%Y-%m-%d")
    weekday                             = date_object.weekday()
    if random.randint(0, 1)==1 and prefix==None:
        prefix                          = '星期'
    elif prefix==None:
        prefix                          = '周'
    return prefix + ["日", "一", "二", "三", "四", "五", "六"][weekday]

class MatchQuery(BaseModel):
    keywords            : str           = Field(default="", description="球队搜索关键词")
    size                : int           = Field(default=10, description="获取几条比赛数据，缺省10   ")
    page                : int           = Field(default=1,  description="查询第几页，缺省1")

class PublisBody(BaseModel):
    match_ids           : str           = Field(..., description="多个match_id英文逗号隔开")


@mcp.tool()
async def post_publish(params:PublisBody) -> str:
    """选择指定比赛发布红单推荐"""
    text                                = await request_post(
        url                             = 'https://172021000008192168068010-7000.vs6.co/expert/posts/publish',
        data                            = params.model_dump(),
        headers                         = {
            'content-type'              : 'application/json',
        },
    )
    return text


@mcp.tool()
async def find_match(params:MatchQuery) -> str:
    """分页获取足球比赛列表数据"""
    # post_json                         = attrs.model_dump()
    now                                 = datetime.now()
    tomorrow                            = now + timedelta(days=1)
    start_date                          = now.strftime('%Y-%m-%d')
    end_date                            = tomorrow.strftime('%Y-%m-%d')
    lottery                             = 'bd'
    keywords                            = params.keywords
    page                                = params.page
    size                                = params.size
    query                               = {
        'start_date':start_date, 'end_date':end_date,
        'bd_open': 1,'bd_open_spf': 1,'order_by': "bd_session_id",
        'lottery': 'bd','keywords':keywords,"page":int(page),"size":int(size),
    }
    data                                = await foot_match_list(params=query)
    # matchs                            = list(filter(lambda x: filter_match(x, lottery), data['list']))
    matchs                              = data['list']
    lottery_type                        = '2'
    lottery_name                        = '北单'
    match_contents                      = []
    for n,match in enumerate(matchs):
        timestr                         = match['foot_match_' + lottery + '_buy_end_time']
        # 两队基础数据
        home                            = {
            'id'                        : match['foot_match_home_team_id'],
            'name'                      : match['foot_match_home_team_name'],
            'sp'                        : "未知",
            'support'                   : match['foot_match_rq_win_support_num'],
            'rank'                      : "未知",
            'score'                     : "未知",
            'recent_total'              : "未知",
            'recent_win'                : "未知",
            'recent_draw'               : "未知",
            'recent_lose'               : "未知",
            'recent_get'                : "未知",
            'recent_lost'               : "未知",
        }
        drow                            = {
            'sp'                        : "未知",
            'support'                   : match['foot_match_spf_draw_support_num'],
        }
        away                            = {
            'id'                        : match['foot_match_visiting_team_id'],
            'name'                      : match['foot_match_visiting_team_name'],
            'sp'                        : "未知",
            'support'                   : match['foot_match_rq_lose_support_num'],
            'rank'                      : "未知",
            'score'                     : "未知",
            'recent_total'              : "未知",
            'recent_win'                : "未知",
            'recent_draw'               : "未知",
            'recent_lose'               : "未知",
            'recent_get'                : "未知",
            'recent_lost'               : "未知",
        }
        # 两队交锋战绩
        analysis                        = await foot_match_analysis(match['foot_match_id'])
        if analysis == False:
            continue
        vs_history                      = {
            'home': 0, 'drow': 0, 'away': 0, 'total': len(analysis['historyVs'])
        }
        for vs in analysis['historyVs']:
            if vs['foot_match_home_final_score'] == vs['foot_match_visiting_final_score']:
                vs_history['drow']      += 1 #平
            elif vs['foot_match_home_team_id'] == home['id'] and vs['foot_match_home_final_score'] > vs['foot_match_visiting_final_score']:
                vs_history['home']      += 1 #主队+主队胜 = 主队胜
            elif vs['foot_match_home_team_id'] != home['id'] and vs['foot_match_home_final_score'] < vs['foot_match_visiting_final_score']:
                vs_history['home']      += 1 #客队+客队胜 = 主队胜
            else:
                vs_history['away']      += 1
        # 赔率获取
        if lottery == 'jc' and match['jc_foot_odds'].get('spf',False):
            odds_name                   = '竞彩赔率'
            home['sp']                  = match['jc_foot_odds']['spf']['data'][0]['odds']
            drow['sp']                  = match['jc_foot_odds']['spf']['data'][1]['odds']
            away['sp']                  = match['jc_foot_odds']['spf']['data'][2]['odds']
        else:
            odds_name                   = '欧洲赔率'
            odds_history                = await foot_odds_history(match['foot_match_id'])
            if odds_history==False or bool(odds_history.get('oupei',False))==False:
                continue
            for odds in odds_history['oupei']:
                if odds['odds_company_id'] == 545:
                    home['sp']          = odds['odds_company_now_win']
                    drow['sp']          = odds['odds_company_now_draw']
                    away['sp']          = odds['odds_company_now_lose']
                    break
        # 球队排名
        match_rank                      = await foot_match_type_rank(match['foot_match_type_id'])
        if match_rank['foot_match_type_common_type'] == 2:
            ctype                       = 'cup'
            rank_list                   = match_rank['cup_rank_score'] or []
        else:
            ctype                       = 'league'
            rank_list                   = match_rank['league_rank_score'] or []
        for m in rank_list:
            if m['foot_team_id'] == home['id'] or m['foot_team_id'] == away['id']:
                team                    = home if m['foot_team_id'] == home['id'] else away
                team['rank']            = m['foot_' + ctype + '_rank_rank'] or '未知'
                team['score']           = m['foot_' + ctype + '_rank_score'] or '未知'
                team['recent_total']    = m['foot_cup_rank_total'] if ctype == 'cup' else m['foot_league_rank_redcard_num']
                team['recent_win']      = m['foot_' + ctype + '_rank_win'] or '无'
                team['recent_draw']     = m['foot_' + ctype + '_rank_draw'] or '无'
                team['recent_lose']     = m['foot_' + ctype + '_rank_lose'] or '无'
                team['recent_get']      = m['foot_' + ctype + '_rank_get'] or '0'
                team['recent_lost']     = m['foot_' + ctype + '_rank_lost'] or '0'
        match_contents.append(f"{n+1}. {home['name']} VS {away['name']}")
        match_contents.append(f"match_id：{match['foot_match_id']}")
        match_contents.append(f"比赛类型：{lottery_name}")
        match_contents.append(f"比赛时间：{timestr} {getWeek(timestr,'周')};")
        match_contents.append(f"{odds_name}：主胜{home['sp']},平{drow['sp']},客胜{away['sp']};")
        match_contents.append(f"主队({home['name']})：小组赛积分 {home['score']}, 排名 {home['rank']};")
        match_contents.append(f"客队({away['name']})：小组赛积分 {away['score']}, 排名 {away['rank']};")
        match_contents.append(f"主队近期战绩：比赛次数 {home['recent_total']}，胜 {home['recent_win']}， 平 {home['recent_draw']}， 负 {home['recent_lose']}，进球 {home['recent_get']}，失球 {home['recent_lost']}；")
        match_contents.append(f"客队近期战绩：比赛次数 {away['recent_total']}，胜 {away['recent_win']}， 平 {away['recent_draw']}， 负 {away['recent_lose']}，进球 {away['recent_get']}，失球 {away['recent_lost']}；")
        match_contents.append(f"两队历史交锋：{vs_history['total']}次，其中主队 胜{vs_history['home']}次，平{vs_history['drow']}次，负{vs_history['away']}次;")
        match_contents.append(f"网友支持：主胜{home['support']/10 :.1f}%,平{drow['support']/10:.1f}%,客胜{away['support']/10:.1f}%;")
        match_contents.append(f"")
    macth_contents                      = '\n'.join(match_contents)
    count                               = data['count']
    return f"以下比赛不要漏掉展示给用户:\n{macth_contents}\n\n共{count}场比赛，当前每页条数(size):{size} 页码(page):{page},共{math.ceil(count/size)}页。请告知用户当前比赛总数与分页信息，提醒可以分页查看更多。"


if __name__ == "__main__":
    mcp.run(transport='stdio')

    



