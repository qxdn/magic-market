import requests
from typing import List, Dict
import time
import click
import logging
import sys

# 配置logging模块
logging.basicConfig(filename="dev.txt", level=logging.DEBUG)
fmt = logging.Formatter(
    "%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(process)d >>> %(message)s"
)
# handler
result_handler = logging.FileHandler("result.txt")
result_handler.setLevel(logging.INFO)
log_handler = logging.FileHandler("log.txt")
log_handler.setLevel(logging.INFO)
debug_handler = logging.FileHandler("debug.txt")
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(fmt)
std_handler = logging.StreamHandler(sys.stdout)
std_handler.setLevel(logging.INFO)

# logger
common_logger = logging.getLogger("common")
common_logger.addHandler(log_handler)
common_logger.addHandler(debug_handler)
common_logger.addHandler(std_handler)
result_logger = logging.getLogger("result")
result_logger.addHandler(result_handler)




MARKET_URL = "https://mall.bilibili.com/mall-magic-c/internet/c2c/v2/list"

HEADERS = {
    "Cookie": "",  #  TODO: 填写cookie
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

CATEGORY_MAP = {
    "全部": "",
    "手办": "2312",
    "模型": "2066",
    "周边": "2331",
    "3C": "2273",
    "福袋": "fudai_cate_id",
}

SORT_MAP = {
    "时间降序": "TIME_DESC",
    "价格升序": "PRICE_ASC",
    "价格降序": "PRICE_DESC",
}


def category2id(category: str):
    return CATEGORY_MAP.get(category, "")


def sort2type(sort: str):
    return SORT_MAP.get(sort, "TIME_DESC")


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
                    f"{c2cItemsName} - {showPrice}元 - {process_url(c2cItemsId)}": showPrice
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
                        f"{c2cItemsName} - {showPrice}元 - {process_url(c2cItemsId)}": showPrice
                    }
                )
                break
    return result


def search(keyword: str, category: str, sort: str):
    nextId = None
    count = 0
    result = []
    while True:
        data = get_market_data(
            next_id=nextId,
            category_filter=category,
            discount_filter=[],
            price_filter=[],
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


@click.command()
@click.option("--keyword", prompt="搜索关键词", help="搜索关键词")
@click.option(
    "--category",
    prompt="请选择分类",
    type=click.Choice(["全部", "手办", "模型", "周边", "3C", "福袋"]),
    default="全部",
)
@click.option(
    "--sort",
    prompt="请选择排序方式",
    type=click.Choice(["时间降序", "价格升序", "价格降序"]),
    default="时间降序",
)
def cli(keyword: str, category: str, sort: str):
    search(keyword, category2id(category), sort2type(sort))


cli()
