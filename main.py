import requests
from typing import List, Dict, Tuple
import time
import logging
import json
import os
import logging.config
from noneprompt import InputPrompt, ListPrompt, Choice, CheckboxPrompt

# 配置logging模块
LOG_CONFIG = "./log_conf.ini"
logging.config.fileConfig(LOG_CONFIG)

common_logger = logging.getLogger("common")
result_logger = logging.getLogger("result")

# 读取配置
DEFAULT_COOKIE = "请填写cookie"
CONFIG_JSON = "./config.json"
if not os.path.exists(CONFIG_JSON):
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump({"cookie": DEFAULT_COOKIE}, f, ensure_ascii=False)

MARKET_URL = "https://mall.bilibili.com/mall-magic-c/internet/c2c/v2/list"

with open(CONFIG_JSON, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
    cookie = CONFIG.get("cookie", "")
    if not cookie or cookie == DEFAULT_COOKIE:
        common_logger.error("请填写cookie")
        exit(1)

HEADERS = {
    "Cookie": cookie,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}


def process_url(c2citemsId):
    return f"https://mall.bilibili.com/neul-next/index.html?page=magic-market_detail&noTitleBar=1&itemsId={c2citemsId}&from=market_index"


def get_market_data(
    category_filter: str = "",
    headers: Dict[str, str] = HEADERS,
    next_id: str = None,
    sort_type: str = "TIME_DESC",
    price_filter: List[str] = [],
    discount_filter: List[str] = [],
):
    response = requests.post(
        MARKET_URL,
        headers=headers,
        json={
            "categoryFilter": category_filter,
            "nextId": next_id,
            "sortType": sort_type,
            "priceFilter": price_filter,
            "discountFilter": discount_filter,
        },
    )
    # print(response.content)
    common_logger.debug(f"response content:{response.content}")
    if response.status_code != 200:
        common_logger.error(f"请求失败，可能被风控，状态码：{response.status_code}")
        exit(1)
    return response.json()


def filter_data(data: dict, keyword: str = None):
    result = []
    if keyword is None:
        return result
    for item in data:
        c2cItemsId = item.get("c2cItemsId", None)
        showPrice = item.get("showPrice", None)
        c2cItemsName = item.get("c2cItemsName", None)
        if keyword in c2cItemsName:
            common_logger.info(
                f"find {keyword}:{c2cItemsName} - {showPrice}元 - {process_url(c2cItemsId)}"
            )
            result.append(
                {
                    "name": c2cItemsName,
                    "price": showPrice,
                    "url": process_url(c2cItemsId),
                }
            )
            continue
        for detail in item.get("detailDtoList", []):
            name = detail.get("name", "")
            if keyword in name:
                common_logger.info(
                    f"find {keyword}:{c2cItemsName} - {showPrice}元 - {process_url(c2cItemsId)}"
                )
                result.append(
                    {
                        "name": c2cItemsName,
                        "price": showPrice,
                        "url": process_url(c2cItemsId),
                    }
                )
                break
    return result


def search(
    keyword: str,
    category: str,
    sort: str,
    price: List[str] = [],
    discount: List[str] = [],
):
    nextId = None
    count = 0
    result = []
    while True:
        data = get_market_data(
            next_id=nextId,
            category_filter=category,
            discount_filter=discount,
            price_filter=price,
            sort_type=sort,
        )

        data = data.get("data", {})
        nextId = data.get("nextId", None)
        if not nextId:
            break
        common_logger.info(f"第{count}页")
        search_result = filter_data(data.get("data", []), keyword)
        if len(search_result) > 0:
            result_logger.info(search_result)
        result.extend(search_result)
        count += 1
        if count % 30 == 0:
            common_logger.info("避免风控，休息半分钟")
            time.sleep(30)

    common_logger.info(f"共找到{len(result)}个结果")
    common_logger.info(result)


# 交互命令行
def cli():
    # 关键词
    keyword: str = InputPrompt("搜索关键词", validator=lambda string: True).prompt()
    # 分类
    category: Tuple[Choice] = ListPrompt(
        "请选择分类",
        choices=[
            Choice(name="全部", data=""),
            Choice(name="手办", data="2312"),
            Choice(name="模型", data="2066"),
            Choice(name="周边", data="2331"),
            Choice(name="3C", data="2273"),
            Choice(name="福袋", data="fudai_cate_id"),
        ],
    ).prompt()
    category: str = category.data
    # 排序
    sort: Choice = ListPrompt(
        "请选择排序方式",
        choices=[
            Choice(name="时间降序", data="TIME_DESC"),
            Choice(name="价格升序", data="PRICE_ASC"),
            Choice(name="价格降序", data="PRICE_DESC"),
        ],
    ).prompt()
    sort: str = sort.data
    # 价格
    price: Tuple[Choice] = CheckboxPrompt(
        "请输入价格区间,默认全部",
        choices=[
            Choice(name="20以下", data="0-2000"),
            Choice(name="20-30", data="2000-3000"),
            Choice(name="30-50", data="3000-5000"),
            Choice(name="50-100", data="5000-10000"),
            Choice(name="100-200", data="10000-20000"),
            Choice(name="200以上", data="20000-0"),
        ],
    ).prompt()
    price: List[str] = [i.data for i in price]
    # 折扣
    discount: Tuple[Choice] = CheckboxPrompt(
        "请选择价格区间，默认全部",
        choices=[
            Choice(name="3折以下", data="0-30"),
            Choice(name="3-5折", data="30-50"),
            Choice(name="5-7折", data="50-70"),
            Choice(name="7折以上", data="70-100"),
        ],
    ).prompt()
    discount: List[str] = [i.data for i in discount]
    search(keyword, category, sort, discount)


cli()
