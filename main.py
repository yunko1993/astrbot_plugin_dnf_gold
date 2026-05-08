import httpx
import re
import time
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.platform import AstrMessageEvent

try:
    from .yxdr_source import build_offer_messages, fetch_yxdr_offers
except ImportError:
    from yxdr_source import build_offer_messages, fetch_yxdr_offers

@register("dnf_gold_monitor", "qingcai", "DNF跨5全平台金价实时看板", "1.1.0")
class DnfGoldPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    @filter.command("查金价")
    async def check_gold(self, event: AstrMessageEvent):
        sender_name = event.get_sender_name()
        yield event.plain_result(f"🔍 正在根据 [{sender_name}] 的指示，扫描 YXDR 跨5聚合行情...")
        
        timestamp = time.strftime("%H:%M:%S")

        async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
            try:
                offers = await fetch_yxdr_offers(client)
                if offers:
                    for message in build_offer_messages(offers, timestamp):
                        yield event.plain_result(message)
                    return

                report = ["【YXDR聚合】暂未抓到有效挂单，尝试 UU898 兜底...\n"]
                report.extend(await self._fetch_uu898_fallback(client))
            except Exception:
                report = []
                report.append("【YXDR聚合】查询失败，尝试 UU898 兜底...\n")
                report.extend(await self._fetch_uu898_fallback(client))

        yield event.plain_result("\n".join(report))

    async def _fetch_uu898_fallback(self, client):
        uu_url = "https://www.uu898.com/newTrade-95-c-3-2325-s25022/"
        report = []
        try:
            r = await client.get(uu_url)
            r.raise_for_status()
            plain = re.sub(r"<[^>]+>", " ", r.text)
            p_chunks = plain.split("免费兑换此商品")
            ratios = []

            for chunk in p_chunks[1:7]:
                match = re.findall(r"1\s*元\s*[=等于]\s*(\d{2}\.?\d*)", chunk)
                if match:
                    value = float(match[0])
                    if 40 < value < 90:
                        ratios.append(value)

            report.append("【UU898兜底】")
            if ratios:
                for value in sorted(set(ratios), reverse=True)[:3]:
                    report.append(f"   - 1:{value} (1亿≈{10000 / value:.1f}元)")
            else:
                report.append("   - 暂未匹配到有效比例")
            report.append(f" 🔗 直达: {uu_url}\n")
        except Exception:
            report.append("【UU898兜底】查询失败\n")
        return report
