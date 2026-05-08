import hashlib
import json
import re
from html import unescape
from urllib.parse import urljoin


YXDR_BASE_URL = "https://www.yxdr.com"
YXDR_KUA5_URL = f"{YXDR_BASE_URL}/bijiaqi/dnf/youxibi/kua5"
DEFAULT_OFFER_LIMIT = 20


def extract_script_src(html: str) -> str:
    match = re.search(r'<script[^>]+src=["\']([^"\']*CoinSale_yxb_[^"\']+)["\']', html, re.I)
    if not match:
        raise ValueError("未找到 YXDR 游戏币通道脚本")
    return urljoin(YXDR_BASE_URL, unescape(match.group(1)))


def extract_json_assignment(script: str, name: str):
    marker = f"window.{name}="
    start = script.find(marker)
    if start < 0:
        raise ValueError(f"未找到 window.{name}")

    value_start = start + len(marker)
    while value_start < len(script) and script[value_start].isspace():
        value_start += 1

    opener = script[value_start]
    closer = {"[": "]", "{": "}"}[opener]
    depth = 0
    in_string = False
    escaped = False

    for index in range(value_start, len(script)):
        char = script[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return json.loads(script[value_start : index + 1].lstrip("\ufeff"))

    raise ValueError(f"window.{name} JSON 不完整")


def build_secret_signature(secret: str, pf_id: int, channel_sign: str) -> str:
    raw = f"{secret}_{pf_id}_{channel_sign}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def offer_ratio(offer: dict) -> float:
    price = float(offer.get("Price") or 0)
    amount = float(offer.get("Amount") or 0)
    money = float(offer.get("Money") or 0)
    trade_type = offer.get("TradeType") or ""

    if price > 0 and ("ling" in trade_type or amount == -1):
        return 1 / price
    if amount > 0 and money > 0:
        return amount / money
    if price > 0:
        return 1 / price
    return 0


def offer_url(offer: dict) -> str:
    return offer.get("BuyUrl") or offer.get("ListUrl") or ""


def format_gold_offer(platform_name: str, offer: dict) -> str:
    ratio = offer_ratio(offer)
    amount = float(offer.get("Amount") or 0)
    amount_text = "充足" if amount == -1 else f"{amount:.0f}万"
    line = f"   - {platform_name} 1:{ratio:.2f} (1亿≈{10000 / ratio:.1f}元) 库存{amount_text}"
    url = offer_url(offer)
    if url:
        line += f" 🔗 {url}"
    return line


def _valid_offer(offer: dict) -> bool:
    ratio = offer_ratio(offer)
    money = float(offer.get("Money") or 0)
    price = float(offer.get("Price") or 0)
    return 40 < ratio < 120 and price > 0 and (money > 0 or offer.get("Amount") == -1)


async def fetch_yxdr_offers(client, page_url: str = YXDR_KUA5_URL, limit: int = DEFAULT_OFFER_LIMIT):
    page = await client.get(page_url)
    page.raise_for_status()

    script_url = extract_script_src(page.text)
    script = await client.get(script_url)
    script.raise_for_status()

    channels = extract_json_assignment(script.text, "bijiaqiChanels")
    result_meta = extract_json_assignment(script.text, "bijiaqiResult")

    secret_response = await client.post(
        f"{YXDR_BASE_URL}/bijia/coinsalesecret",
        json={"GId": result_meta.get("GId", 1838), "GsId": result_meta.get("GsId")},
        headers={"Referer": page_url},
    )
    secret_response.raise_for_status()
    secret_info = secret_response.json()

    offers = []
    for channel in channels:
        channel_data = json.loads(channel["data"])
        if channel_data.get("CoinNo") != "yxb":
            continue

        pf_id = channel_data["PfId"]
        response = await client.post(
            f"{YXDR_BASE_URL}/bijia/coinsale",
            json={
                "data": channel["data"],
                "sign": channel["sign"],
                "cross": 0,
                "dnfCross": 1,
                "time": secret_info["time"],
                "secret": build_secret_signature(secret_info["secret"], pf_id, channel["sign"]),
            },
            headers={"Referer": page_url},
        )
        if response.status_code != 200:
            continue

        data = response.json()
        if not data.get("success"):
            continue

        platform_name = channel_data.get("PfName", f"平台{pf_id}")
        for offer in data.get("data") or []:
            if _valid_offer(offer):
                offers.append({"platform": platform_name, "offer": offer, "ratio": offer_ratio(offer)})

    offers.sort(key=lambda item: item["ratio"], reverse=True)
    return offers[:limit]
