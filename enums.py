from enum import Enum,unique

@unique
class CategoryFilter(Enum):
    ALL = ""
    FIGURE = 2312  # 手办
    MODEL = 2066 # 模型
    MERCH = 2331 # 周边
    THREEC = 2273 # 3C
    FUDAI = "fudai_cate_id" # 福袋


@unique
class SortType(Enum):
    TIME_DESC = "TIME_DESC"
    PRICE_DESC = "PRICE_DESC"
    PRICE_ASC = "PRICE_ASC"

@unique
class PriceFilter(Enum):
    UNDER_2000 = "0-2000" # 0-20
    BETWEEN_200 = "2000-3000" # 20-30
    BETWEEN_3000_5000 = "3000-5000" # 30-50
    BETWEEN_5000_10000 = "5000-10000" # 50-100
    BETWEEN_10000_20000 = "10000-20000" # 100-200
    OVER_20000 = "20000-0" # 200+

@unique
class DiscountFilter(Enum):
    UNDER_30 = "0-30" # 3折以下
    BETWEEN_30_50 = "30-50" # 3-5折
    BETWEEN_50_70 = "50-70" # 5-7折
    OVER_70 = "70-100" # 7折以上