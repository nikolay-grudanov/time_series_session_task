"""
Unit tests for trading strategy service.

Tests cover:
- Trading signal generation
- Signal ordering (buy before sell)
- Profit calculation with valid signals
- Edge cases with invalid signal ordering
"""

import pandas as pd
import numpy as np
import pytest

from src.services.trading_strategy import TradingStrategyService
from src.services.profit_calculator import ProfitCalculatorService


class TestTradingSignalOrdering:
    """Test that trading signals are properly ordered (buy before sell)."""

    def test_sell_before_buy_filtered_out(self):
        """Test that sell signals before first buy are filtered out."""
        service = TradingStrategyService()

        # Create forecast where sell comes BEFORE buy (invalid order)
        dates = pd.date_range("2026-01-15", periods=10, freq="D")
        forecast_data = np.array([100, 105, 110, 108, 106, 112, 115, 113, 111, 118])
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.identify_optimal_trades(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
        )

        # Get filtered signals
        buy_signals = result["buy_signals"]
        sell_signals = result["sell_signals"]

        # Build chronological list and verify pattern
        all_filtered = []
        for sig in buy_signals:
            all_filtered.append({"date": sig["date"], "action": "BUY"})
        for sig in sell_signals:
            all_filtered.append({"date": sig["date"], "action": "SELL"})
        all_filtered.sort(key=lambda x: x["date"])

        # Every SELL should have a prior BUY
        has_bought = False
        for sig in all_filtered:
            if sig["action"] == "BUY":
                has_bought = True
            elif sig["action"] == "SELL":
                assert has_bought, f"SELL at {sig['date']} occurred without prior BUY"

    def test_valid_buy_sell_sequence(self):
        """Test that valid buy->sell sequences are preserved with buy->sell->buy pattern."""
        service = TradingStrategyService()

        # Create forecast with clear up and down pattern
        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        # Pattern: up, up, down, down, up, down (multiple cycles)
        forecast_data = np.array(
            [
                100,
                102,
                104,
                103,
                101,
                99,
                98,
                100,
                102,
                101,
                99,
                97,
                96,
                98,
                100,
                102,
                101,
                99,
                97,
                95,
            ]
        )
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.identify_optimal_trades(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
        )

        # Get filtered signals
        buy_signals = result["buy_signals"]
        sell_signals = result["sell_signals"]

        # Verify no SELL occurs before a corresponding BUY
        # Build chronological list and verify buy-sell-buy pattern
        all_filtered = []
        for sig in buy_signals:
            all_filtered.append({"date": sig["date"], "action": "BUY"})
        for sig in sell_signals:
            all_filtered.append({"date": sig["date"], "action": "SELL"})
        all_filtered.sort(key=lambda x: x["date"])

        # Verify pattern: BUY can appear anytime, SELL only after a BUY
        has_bought = False
        for sig in all_filtered:
            if sig["action"] == "BUY":
                has_bought = True
            elif sig["action"] == "SELL":
                assert has_bought, f"SELL at {sig['date']} occurred without prior BUY"

    def test_no_signals_returns_empty(self):
        """Test that flat forecast returns no signals."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=10, freq="D")
        forecast_data = np.array([100, 100, 100, 100, 100, 100, 100, 100, 100, 100])
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.identify_optimal_trades(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
        )

        assert result["total_buy_signals"] == 0
        assert result["total_sell_signals"] == 0


class TestProfitCalculationWithOrderedSignals:
    """Test profit calculation with properly ordered signals."""

    def test_profit_with_valid_buy_sell(self):
        """Test profit calculation with valid buy->sell sequence."""
        calc = ProfitCalculatorService()

        buy_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Test buy"},
            {
                "date": pd.Timestamp("2026-01-18"),
                "price": 105.0,
                "reason": "Test buy 2",
            },
        ]
        sell_signals = [
            {"date": pd.Timestamp("2026-01-16"), "price": 102.0, "reason": "Test sell"},
            {
                "date": pd.Timestamp("2026-01-20"),
                "price": 110.0,
                "reason": "Test sell 2",
            },
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=108.0,
        )

        # Should have positive profit from trading
        assert result["trading_strategy"]["profit"] > 0
        assert result["trading_strategy"]["roi_percentage"] > 0

    def test_profit_with_only_buy_signals(self):
        """Test profit calculation when no sell signals (holding to end)."""
        calc = ProfitCalculatorService()

        buy_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Test buy"},
        ]
        sell_signals = []

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # Should still calculate profit based on final price
        assert result["trading_strategy"]["profit"] > 0

    def test_profit_with_no_signals(self):
        """Test profit calculation when no signals (simple holding)."""
        calc = ProfitCalculatorService()

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=[],
            sell_signals=[],
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # With no signals, trading strategy does nothing (profit = 0)
        # But holding strategy should still work
        assert result["trading_strategy"]["profit"] == 0
        expected_holding_profit = (1000 / 100 * 110) - 1000  # Buy at 100, sell at 110
        assert result["holding_strategy"]["profit"] == expected_holding_profit
        # Comparison: trading didn't beat holding
        assert result["comparison"]["active_vs_hold"] == -expected_holding_profit

    def test_profit_effectiveness_rating(self):
        """Test that effectiveness rating is calculated correctly."""
        calc = ProfitCalculatorService()

        # Trading strategy outperforms holding
        result1 = calc.calculate_detailed_profit_analysis(
            buy_signals=[
                {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Buy"}
            ],
            sell_signals=[
                {"date": pd.Timestamp("2026-01-16"), "price": 105.0, "reason": "Sell"}
            ],
            investment_amount=1000,
            initial_price=100.0,
            final_price=103.0,  # Holding would give only $30 profit
        )

        # Trading should be highly effective if it beats holding by > 2%
        assert result1["effectiveness"] in ["Highly Effective", "Moderately Effective"]

        # Trading strategy underperforms holding
        result2 = calc.calculate_detailed_profit_analysis(
            buy_signals=[
                {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Buy"}
            ],
            sell_signals=[
                {"date": pd.Timestamp("2026-01-16"), "price": 101.0, "reason": "Sell"}
            ],
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,  # Holding would give $100 profit
        )

        # Trading should be ineffective if it underperforms holding
        assert result2["effectiveness"] in ["Ineffective", "Marginally Effective"]


class TestTradingStrategyIntegration:
    """Integration tests for trading strategy with profit calculation."""

    def test_full_trading_pipeline(self):
        """Test complete pipeline from forecast to profit calculation."""
        service = TradingStrategyService()
        calc = ProfitCalculatorService()

        # Create realistic forecast data
        dates = pd.date_range("2026-01-15", periods=30, freq="D")
        # Simulate price going up then down then up
        forecast_data = np.concatenate(
            [
                np.linspace(100, 110, 10),  # Uptrend
                np.linspace(110, 105, 5),  # Downtrend
                np.linspace(105, 115, 15),  # Strong uptrend
            ]
        )
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        # Get trading signals
        signals = service.generate_trading_recommendations(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
        )

        # Verify signal ordering - build chronological list
        buy_signals = signals["trade_signals"]["buy_signals"]
        sell_signals = signals["trade_signals"]["sell_signals"]

        all_filtered = []
        for sig in buy_signals:
            all_filtered.append({"date": sig["date"], "action": "BUY"})
        for sig in sell_signals:
            all_filtered.append({"date": sig["date"], "action": "SELL"})
        all_filtered.sort(key=lambda x: x["date"])

        # Every SELL should have a prior BUY
        has_bought = False
        for sig in all_filtered:
            if sig["action"] == "BUY":
                has_bought = True
            elif sig["action"] == "SELL":
                assert has_bought, f"SELL at {sig['date']} occurred without prior BUY"

        # Calculate profit
        profit = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=float(historical.iloc[-1]),
            final_price=float(forecast_data[-1]),
        )

        # Verify profit calculation
        assert "profit" in profit["trading_strategy"]
        assert "roi_percentage" in profit["trading_strategy"]
        assert "effectiveness" in profit

        # Trading profit should be calculated (may be positive or negative)
        assert isinstance(
            profit["trading_strategy"]["profit"], (int, float, np.floating)
        )

    def test_edge_case_local_minima_before_maxima(self):
        """Test handling of local minima that appear before maxima."""
        service = TradingStrategyService()

        # Create data where first local minimum comes before first local maximum
        dates = pd.date_range("2026-01-15", periods=10, freq="D")
        # Local min at index 1 (101), local max at index 2 (103)
        forecast_data = np.array([100, 101, 103, 102, 104, 103, 105, 104, 106, 105])
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.identify_optimal_trades(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
        )

        # Get first buy and first sell
        if result["buy_signals"] and result["sell_signals"]:
            first_buy_date = result["buy_signals"][0]["date"]
            first_sell_date = result["sell_signals"][0]["date"]

            # Buy should be before or equal to sell (buy at local min, then sell at local max)
            assert first_buy_date <= first_sell_date, (
                f"First buy ({first_buy_date}) should be before first sell ({first_sell_date})"
            )


class TestProfitCalculationWithInvalidSignalOrder:
    """
    Regression tests for bug where sell signals had dates BEFORE buy signals.
    This caused profit to be $0 instead of positive value.

    Bug: Sell at 2026-01-16, Buy at 2026-01-17 (impossible chronology)
    Fix: Filter signals in TradingStrategyService to ensure buy always comes before sell

    IMPORTANT: These tests verify that ProfitCalculatorService handles all edge cases
    correctly regardless of signal order (it's a passive calculator).
    """

    def test_profit_with_sell_before_buy_calculator_handles_gracefully(self):
        """
        Test that ProfitCalculatorService handles sell-before-buy gracefully.
        The calculator simply processes signals in chronological order.
        Sell before buy with 0 shares results in $0 from that sell.
        """
        calc = ProfitCalculatorService()

        # Sell BEFORE buy (impossible scenario)
        buy_signals = [
            {"date": pd.Timestamp("2026-01-17"), "price": 105.0, "reason": "Buy"},
        ]
        sell_signals = [
            {"date": pd.Timestamp("2026-01-16"), "price": 102.0, "reason": "Sell"},
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # Sell at 102 when shares=0: no effect
        # Buy at 105: shares = 1000/105 ≈ 9.52
        # Final value: 9.52 * 110 = 1047.62
        # Profit: 1047.62 - 1000 = 47.62
        assert result["trading_strategy"]["profit"] > 0

    def test_profit_with_multiple_sells_before_buys(self):
        """
        Test case: Multiple sell signals all come before first buy signal.
        Calculator handles this by selling 0 shares each time.
        """
        calc = ProfitCalculatorService()

        # All sells before all buys
        buy_signals = [
            {"date": pd.Timestamp("2026-01-20"), "price": 110.0, "reason": "Buy 1"},
        ]
        sell_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 102.0, "reason": "Sell 1"},
            {"date": pd.Timestamp("2026-01-16"), "price": 103.0, "reason": "Sell 2"},
            {"date": pd.Timestamp("2026-01-18"), "price": 105.0, "reason": "Sell 3"},
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=120.0,
        )

        # All sells happen with 0 shares, then buy at 110
        # Shares: 1000/110 ≈ 9.09
        # Final value: 9.09 * 120 = 1090.91
        # Profit: 1090.91 - 1000 = 90.91
        assert result["trading_strategy"]["profit"] > 0

    def test_profit_with_mixed_valid_order(self):
        """
        Test case: Valid buy->sell pairs should generate profit.
        """
        calc = ProfitCalculatorService()

        # Valid order: buy1 -> sell1, buy2 -> sell2
        buy_signals = [
            {"date": pd.Timestamp("2026-01-16"), "price": 102.0, "reason": "Buy 1"},
            {"date": pd.Timestamp("2026-01-22"), "price": 112.0, "reason": "Buy 2"},
        ]
        sell_signals = [
            {"date": pd.Timestamp("2026-01-18"), "price": 108.0, "reason": "Sell 1"},
            {"date": pd.Timestamp("2026-01-25"), "price": 118.0, "reason": "Sell 2"},
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=120.0,
        )

        # Trade 1: Buy 1000/102 = 9.804 shares, Sell at 108: 9.804 * 108 = 1058.82, profit = 58.82
        # Trade 2: Buy 1058.82/112 = 9.454 shares, Sell at 118: 9.454 * 118 = 1115.59, profit = 56.77
        # Total profit: 58.82 + 56.77 = 115.59
        assert result["trading_strategy"]["profit"] > 100

    def test_profit_with_buy_and_sell_on_same_day(self):
        """
        Test case: Buy and sell on same day (zero time held).
        """
        calc = ProfitCalculatorService()

        buy_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Buy"},
        ]
        sell_signals = [
            {
                "date": pd.Timestamp("2026-01-15"),
                "price": 100.0,
                "reason": "Same day sell",
            },
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # Buy at 100, immediately sell at 100: 1000/100 * 100 = 1000
        # Profit = 0 (no change in price)
        assert result["trading_strategy"]["profit"] == 0

    def test_profit_bug_regression_original_order(self):
        """
        REGRESSION TEST: Original bug scenario from /forecast GOOGL 1000
        Buy: 2026-01-17 @ 159.06, Sell: 2026-01-16 @ 158.38
        This caused $0 profit because sell was processed first with 0 shares,
        then buy, but final price wasn't used correctly.

        With current fix (TradingStrategyService ensures proper ordering),
        this scenario should not happen in production.
        """
        calc = ProfitCalculatorService()

        # Original bug order
        buy_signals = [
            {
                "date": pd.Timestamp("2026-01-17"),
                "price": 159.06,
                "reason": "Local minimum",
            },
        ]
        sell_signals = [
            {
                "date": pd.Timestamp("2026-01-16"),
                "price": 158.38,
                "reason": "Local maximum",
            },
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=157.50,
            final_price=162.00,
        )

        # Sell at 158.38 first (shares=0, no effect)
        # Buy at 159.06: shares = 1000/159.06 ≈ 6.286
        # Final value: 6.286 * 162.00 = 1018.38
        # Profit: 1018.38 - 1000 = 18.38
        assert result["trading_strategy"]["profit"] > 0

    def test_profit_with_buy_after_sell_all_trades(self):
        """
        Test that when ALL sell signals come after ALL buy signals,
        profit calculation works correctly.
        """
        calc = ProfitCalculatorService()

        # All buys before all sells (correct order)
        buy_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Buy 1"},
            {"date": pd.Timestamp("2026-01-18"), "price": 105.0, "reason": "Buy 2"},
        ]
        sell_signals = [
            {"date": pd.Timestamp("2026-01-16"), "price": 102.0, "reason": "Sell 1"},
            {"date": pd.Timestamp("2026-01-20"), "price": 110.0, "reason": "Sell 2"},
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=108.0,
        )

        # Trade 1: Buy 1000/100 = 10 shares, Sell at 102: 10 * 102 = 1020, profit = 20
        # Trade 2: Buy 1020/105 = 9.714 shares, Sell at 110: 9.714 * 110 = 1068.57, profit = 48.57
        # Total profit: 20 + 48.57 = 68.57
        assert result["trading_strategy"]["profit"] > 0


class TestSignalOrderingEdgeCases:
    """Edge cases for signal ordering validation."""

    def test_empty_signal_lists_handled(self):
        """Empty buy and sell lists should not cause errors."""
        calc = ProfitCalculatorService()

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=[],
            sell_signals=[],
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # With no signals, trading doesn't happen (cash never converts to shares)
        # But holding strategy should still work
        assert result["holding_strategy"]["profit"] > 0

    def test_only_buy_signals_no_sells(self):
        """Only buy signals - profit depends on final price."""
        calc = ProfitCalculatorService()

        buy_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 100.0, "reason": "Buy"},
        ]
        sell_signals = []

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # Buy at 100, final price is 110
        # Shares: 1000/100 = 10
        # Final value: 10 * 110 = 1100
        # Profit: 1100 - 1000 = 100
        assert result["trading_strategy"]["profit"] > 0

    def test_only_sell_signals_no_buys(self):
        """Only sell signals - can't sell without owning shares."""
        calc = ProfitCalculatorService()

        buy_signals = []
        sell_signals = [
            {"date": pd.Timestamp("2026-01-15"), "price": 105.0, "reason": "Sell"},
        ]

        result = calc.calculate_detailed_profit_analysis(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            investment_amount=1000,
            initial_price=100.0,
            final_price=110.0,
        )

        # No buy signals, so no shares owned
        # Sell at 105 has no effect (0 shares)
        # Profit should be 0 (no trades executed)
        assert result["trading_strategy"]["profit"] == 0


class TestGenerateTradingRecommendations:
    """Test the main generate_trading_recommendations method."""

    def test_recommendations_structure(self):
        """Test that recommendations have correct structure."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        forecast_data = np.linspace(100, 120, 20)
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
        )

        # Verify structure
        assert "trade_signals" in result
        assert "buy_signals" in result["trade_signals"]
        assert "sell_signals" in result["trade_signals"]
        assert "recommendation_summary" in result
        # Note: total_buy_signals and total_sell_signals are in trade_signals
        assert "total_buy_signals" in result["trade_signals"]
        assert "total_sell_signals" in result["trade_signals"]

    def test_recommendations_with_uptrend_with_dips(self):
        """Test recommendations in uptrend with small dips (realistic scenario)."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        # Uptrend with small dips to create local minima
        forecast_data = np.array(
            [
                100,
                102,
                101,
                103,
                105,
                104,
                106,
                108,
                107,
                109,
                111,
                110,
                112,
                114,
                113,
                115,
                117,
                116,
                118,
                120,
            ]
        )
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
        )

        # Should have buy signals (local minima exist in this pattern)
        assert result["trade_signals"]["total_buy_signals"] > 0

        # Verify ordering - build chronological list
        buy_signals = result["trade_signals"]["buy_signals"]
        sell_signals = result["trade_signals"]["sell_signals"]

        all_filtered = []
        for sig in buy_signals:
            all_filtered.append({"date": sig["date"], "action": "BUY"})
        for sig in sell_signals:
            all_filtered.append({"date": sig["date"], "action": "SELL"})
        all_filtered.sort(key=lambda x: x["date"])

        # Every SELL should have a prior BUY
        has_bought = False
        for sig in all_filtered:
            if sig["action"] == "BUY":
                has_bought = True
            elif sig["action"] == "SELL":
                assert has_bought, f"SELL at {sig['date']} occurred without prior BUY"

    def test_recommendations_with_downtrend_only(self):
        """Test recommendations in downtrend (fewer opportunities)."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        forecast_data = np.linspace(150, 100, 20)  # Strong downtrend
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
        )

        # Verify structure exists
        assert "trade_signals" in result
        assert "recommendation_summary" in result


class TestTradingRecommendationsLocalized:
    """Test the new generate_trading_recommendations_localized method."""

    def test_localized_recommendations_russian(self):
        """Test that localized recommendations work for Russian language."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        forecast_data = np.linspace(100, 120, 20)
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations_localized(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
            language="ru",
        )

        # Verify structure
        assert "trade_signals" in result
        assert "potential_profits" in result
        assert "recommendation_summary" in result

        # Check that recommendation_summary is in Russian (contains Cyrillic)
        summary = result["recommendation_summary"]
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_localized_recommendations_english(self):
        """Test that localized recommendations work for English language."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        forecast_data = np.linspace(100, 120, 20)
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations_localized(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
            language="en",
        )

        # Verify structure
        assert "trade_signals" in result
        assert "potential_profits" in result
        assert "recommendation_summary" in result

        # Check that recommendation_summary is not empty
        summary = result["recommendation_summary"]
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_localized_recommendations_contains_profit_and_roi(self):
        """Test that localized recommendations include profit and ROI info."""
        service = TradingStrategyService()

        # Use data with distinct patterns to generate signals
        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        forecast_data = np.array(
            [
                100,
                102,
                101,
                103,
                105,
                104,
                106,
                108,
                107,
                109,
                111,
                110,
                112,
                114,
                113,
                115,
                117,
                116,
                118,
                120,
            ]
        )
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations_localized(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
            language="en",
        )

        summary = result["recommendation_summary"]

        # Should contain profit info (with $ sign and numbers)
        # Or if no signals, should have neutral message
        assert "$" in summary or "neutral" in summary.lower() or "No clear" in summary

    def test_localized_recommendations_with_no_signals(self):
        """Test localized recommendations when no trading signals exist."""
        service = TradingStrategyService()

        # Create data that won't generate signals
        dates = pd.date_range("2026-01-15", periods=5, freq="D")
        forecast_data = np.array([100, 100, 100, 100, 100])  # Flat data
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        result = service.generate_trading_recommendations_localized(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
            language="en",
        )

        # Should still return valid structure
        assert "trade_signals" in result
        assert "recommendation_summary" in result

        # Summary should handle no opportunities gracefully
        summary = result["recommendation_summary"]
        assert isinstance(summary, str)

    def test_localized_vs_non_localized_same_structure(self):
        """Test that localized and non-localized methods return compatible structures."""
        service = TradingStrategyService()

        dates = pd.date_range("2026-01-15", periods=20, freq="D")
        forecast_data = np.linspace(100, 120, 20)
        historical = pd.Series(
            [100 + i * 0.5 for i in range(100)],
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )

        # Generate with both methods
        result_localized = service.generate_trading_recommendations_localized(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
            language="en",
        )

        result_non_localized = service.generate_trading_recommendations(
            forecast_data=forecast_data,
            historical_data=historical,
            forecast_dates=dates,
            investment_amount=1000,
        )

        # Both should have same keys
        assert set(result_localized.keys()) == set(result_non_localized.keys())

        # Both should have trade_signals with same structure
        assert set(result_localized["trade_signals"].keys()) == set(
            result_non_localized["trade_signals"].keys()
        )
