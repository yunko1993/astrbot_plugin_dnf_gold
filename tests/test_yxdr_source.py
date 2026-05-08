import unittest

from yxdr_source import (
    DEFAULT_OFFER_LIMIT,
    build_secret_signature,
    extract_json_assignment,
    extract_script_src,
    format_gold_offer,
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
        offer = {"Price": 0.016808, "Amount": 149783.0, "Money": 2517.55, "Seller": "abc"}

        self.assertEqual(
            "   - DD373 1:59.50 (1亿≈168.1元) 库存149783万",
            format_gold_offer("DD373", offer),
        )


if __name__ == "__main__":
    unittest.main()
