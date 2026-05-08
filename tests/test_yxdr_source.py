import unittest

from yxdr_source import (
    DEFAULT_OFFER_LIMIT,
    build_secret_signature,
    build_offer_messages,
    extract_json_assignment,
    extract_script_src,
    format_gold_offer,
    offer_url,
    offer_ratio,
)


class YxdrSourceTest(unittest.TestCase):
    def test_default_offer_limit_is_twenty(self):
        self.assertEqual(20, DEFAULT_OFFER_LIMIT)

    def test_extract_script_src_finds_coin_sale_script(self):
        html = '<script src="/cate/1838/CoinSale_yxb_215_0.js?ver=935"></script>'

        self.assertEqual(
            "https://www.yxdr.com/cate/1838/CoinSale_yxb_215_0.js?ver=935",
            extract_script_src(html),
        )

    def test_extract_json_assignment_reads_window_array(self):
        script = 'window.bijiaqiChanels=[{"data":"{}","sign":"abc"}];\nwindow.other=1;'

        self.assertEqual([{"data": "{}", "sign": "abc"}], extract_json_assignment(script, "bijiaqiChanels"))

    def test_build_secret_signature_matches_yxdr_rule(self):
        self.assertEqual(
            "99497d5cc64b575bdba8d549f05d47d1",
            build_secret_signature("secret-value", 40, "channel-sign"),
        )

    def test_offer_ratio_prefers_unit_price_for_retail_trade(self):
        offer = {"Price": 0.016808, "Amount": 149783.0, "Money": 2517.55, "TradeType": "shang|ling"}

        self.assertAlmostEqual(59.4955, offer_ratio(offer), places=4)

    def test_format_gold_offer_shows_platform_ratio_and_100m_price(self):
        offer = {
            "Price": 0.016808,
            "Amount": 149783.0,
            "Money": 2517.55,
            "Seller": "abc",
            "BuyUrl": "https://order.dd373.com/default/buy_form.html?id=1",
        }

        self.assertEqual(
            "   - DD373 1:59.50 (1亿≈168.1元) 库存149783万 🔗 https://order.dd373.com/default/buy_form.html?id=1",
            format_gold_offer("DD373", offer),
        )

    def test_offer_url_falls_back_to_list_url(self):
        offer = {"ListUrl": "https://www.dd373.com/s/example.html"}

        self.assertEqual("https://www.dd373.com/s/example.html", offer_url(offer))

    def test_build_offer_messages_splits_top_twenty_into_five_item_messages(self):
        items = []
        for index in range(20):
            items.append(
                {
                    "platform": "DD373",
                    "offer": {
                        "Price": 0.016,
                        "Amount": 1000,
                        "Money": 16,
                        "BuyUrl": f"https://example.com/{index}",
                    },
                }
            )

        messages = build_offer_messages(items, "09:30:00")

        self.assertEqual(4, len(messages))
        self.assertIn("【YXDR聚合 Top 20 1-5】", messages[0])
        self.assertIn("【YXDR聚合 Top 20 16-20】", messages[3])
        self.assertEqual(5, messages[0].count("https://example.com/"))


if __name__ == "__main__":
    unittest.main()
