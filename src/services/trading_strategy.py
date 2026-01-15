"""
Service for generating buy/sell recommendations.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader

logger = logging.getLogger(__name__)


class TradingStrategyService:
    """
    Service for generating trading recommendations based on forecast data.
    """

    def __init__(self):
        pass

    def identify_optimal_trades(
        self,
        forecast_data: np.ndarray,
        historical_data: pd.Series,
        forecast_dates: pd.DatetimeIndex,
    ) -> dict[str, Any]:
        """
        Identifies optimal buy/sell days based on forecast data.

        Args:
            forecast_data: Forecasted stock prices
            historical_data: Historical stock price data
            forecast_dates: Dates corresponding to forecast data

        Returns:
            Dictionary with trading recommendations
        """
        logger.info("Identifying optimal buy/sell days based on forecast data")

        # Convert to pandas Series for easier manipulation
        forecast_series = pd.Series(forecast_data, index=forecast_dates)

        # Calculate rolling statistics to identify trends
        short_window = 3  # 3-day window for short-term trend
        long_window = 7  # 7-day window for long-term trend

        # Calculate rolling averages
        forecast_series_short_avg = forecast_series.rolling(window=short_window).mean()
        forecast_series_long_avg = forecast_series.rolling(window=long_window).mean()

        # Identify potential buy/sell signals
        buy_signals = []
        sell_signals = []

        # Look for crossover signals (when short-term average crosses above/below long-term average)
        for i in range(max(short_window, long_window), len(forecast_series)):
            date = forecast_series.index[i]
            current_price = forecast_series.iloc[i]

            # Check for buy signal (short-term average crosses above long-term average)
            if (
                i >= short_window
                and i >= long_window
                and forecast_series_short_avg.iloc[i - 1]
                <= forecast_series_long_avg.iloc[i - 1]
                and forecast_series_short_avg.iloc[i] > forecast_series_long_avg.iloc[i]
            ):
                buy_signals.append(
                    {
                        "date": date,
                        "price": current_price,
                        "reason": "Short-term trend crossed above long-term trend",
                    }
                )

            # Check for sell signal (short-term average crosses below long-term average)
            elif (
                i >= short_window
                and i >= long_window
                and forecast_series_short_avg.iloc[i - 1]
                >= forecast_series_long_avg.iloc[i - 1]
                and forecast_series_short_avg.iloc[i] < forecast_series_long_avg.iloc[i]
            ):
                sell_signals.append(
                    {
                        "date": date,
                        "price": current_price,
                        "reason": "Short-term trend crossed below long-term trend",
                    }
                )

        # Also identify local minima (potential buy points) and maxima (potential sell points)
        for i in range(1, len(forecast_series) - 1):
            prev_price = forecast_series.iloc[i - 1]
            curr_price = forecast_series.iloc[i]
            next_price = forecast_series.iloc[i + 1]

            date = forecast_series.index[i]

            # Local minimum (potential buy point)
            if prev_price > curr_price < next_price:
                # Check if it's not already in buy_signals
                if not any(
                    pd.Timestamp(sig["date"]).date() == date.date()
                    for sig in buy_signals
                ):
                    buy_signals.append(
                        {
                            "date": date,
                            "price": curr_price,
                            "reason": "Local minimum in forecast",
                        }
                    )

            # Local maximum (potential sell point)
            elif prev_price < curr_price > next_price:
                # Check if it's not already in sell_signals
                if not any(
                    pd.Timestamp(sig["date"]).date() == date.date()
                    for sig in sell_signals
                ):
                    sell_signals.append(
                        {
                            "date": date,
                            "price": curr_price,
                            "reason": "Local maximum in forecast",
                        }
                    )

        # Sort signals by date
        buy_signals.sort(key=lambda x: x["date"])
        sell_signals.sort(key=lambda x: x["date"])

        # Filter signals to ensure we have alternating buy/sell patterns starting with buy
        # This ensures we never sell before buying
        filtered_buy_signals = []
        filtered_sell_signals = []

        if not buy_signals and not sell_signals:
            # No signals at all
            pass
        elif not buy_signals:
            # Only sell signals - skip them all (can't sell without buying first)
            logger.info(
                "Only sell signals found, skipping all as no buy occurred first"
            )
        elif not sell_signals:
            # Only buy signals - keep them
            filtered_buy_signals = buy_signals[:5]
        else:
            # Both buy and sell signals exist
            # Merge and sort by date
            all_signals = []
            for sig in buy_signals:
                all_signals.append(
                    {
                        "date": sig["date"],
                        "price": sig["price"],
                        "action": "BUY",
                        "reason": sig["reason"],
                    }
                )
            for sig in sell_signals:
                all_signals.append(
                    {
                        "date": sig["date"],
                        "price": sig["price"],
                        "action": "SELL",
                        "reason": sig["reason"],
                    }
                )

            # Sort by date
            all_signals.sort(key=lambda x: x["date"])

            # Filter to ensure buy -> sell -> buy -> sell pattern
            has_bought = False
            for sig in all_signals:
                if sig["action"] == "BUY":
                    filtered_buy_signals.append(sig)
                    has_bought = True
                elif sig["action"] == "SELL" and has_bought:
                    # Only add sell if we've already bought
                    filtered_sell_signals.append(sig)
                    has_bought = False  # Reset after selling

        # Limit to top 5 buy and sell signals
        top_buy_signals = filtered_buy_signals[:5]
        top_sell_signals = filtered_sell_signals[:5]

        result = {
            "buy_signals": top_buy_signals,
            "sell_signals": top_sell_signals,
            "total_buy_signals": len(top_buy_signals),
            "total_sell_signals": len(top_sell_signals),
            "strategy_summary": self._generate_strategy_summary(
                top_buy_signals, top_sell_signals
            ),
        }

        logger.info(
            f"Identified {len(top_buy_signals)} buy signals and {len(top_sell_signals)} sell signals"
        )
        return result

    def _generate_strategy_summary(
        self, buy_signals: list[dict], sell_signals: list[dict]
    ) -> str:
        """
        Generates a summary of the trading strategy.

        Args:
            buy_signals: List of buy signals
            sell_signals: List of sell signals

        Returns:
            Strategy summary string
        """
        if not buy_signals and not sell_signals:
            return "No clear trading opportunities identified in the forecast."

        summary_parts = []

        if buy_signals:
            buy_dates = [sig["date"].strftime("%Y-%m-%d") for sig in buy_signals]
            summary_parts.append(f"Buy opportunities on: {', '.join(buy_dates)}")

        if sell_signals:
            sell_dates = [sig["date"].strftime("%Y-%m-%d") for sig in sell_signals]
            summary_parts.append(f"Sell opportunities on: {', '.join(sell_dates)}")

        return "; ".join(summary_parts)

    def generate_trading_recommendations_localized(
        self,
        forecast_data: np.ndarray,
        historical_data: pd.Series,
        forecast_dates: pd.DatetimeIndex,
        investment_amount: float,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Generates formatted trading recommendations with localization.

        Args:
            forecast_data: Forecasted stock prices
            historical_data: Historical stock price data
            forecast_dates: Dates corresponding to forecast data
            investment_amount: Amount to invest
            language: User's language code (ru, en, etc.)

        Returns:
            Dictionary with formatted trading recommendations
        """
        logger.info(
            f"Generating localized trading recommendations for language: {language}"
        )

        # Identify optimal trades
        trade_signals = self.identify_optimal_trades(
            forecast_data, historical_data, forecast_dates
        )

        # Calculate potential profits based on signals
        potential_profits = self.calculate_potential_profits(
            trade_signals["buy_signals"],
            trade_signals["sell_signals"],
            investment_amount,
        )

        # Format recommendations with localization
        formatted_text = self._format_recommendations_with_i18n(
            trade_signals, potential_profits, language
        )

        recommendations = {
            "trade_signals": trade_signals,
            "potential_profits": potential_profits,
            "investment_amount": investment_amount,
            "recommendation_summary": formatted_text,
        }

        logger.info("Localized trading recommendations generated successfully")
        return recommendations

    def _format_recommendations_with_i18n(
        self,
        trade_signals: dict,
        potential_profits: dict,
        language: str,
    ) -> str:
        """
        Formats trading recommendations with i18n support.

        Args:
            trade_signals: Trade signals dictionary
            potential_profits: Potential profits dictionary
            language: User's language code

        Returns:
            Formatted recommendation string
        """
        loader = MessageLoader()
        lines = []

        # Check if there are any signals
        if not trade_signals["buy_signals"] and not trade_signals["sell_signals"]:
            lines.append(loader.get(MessageKey.no_opportunities, language))
            lines.append(loader.get(MessageKey.market_neutral, language))
            return "\n\n".join(lines)

        # Add profit and ROI info
        profit_line = loader.get(
            MessageKey.profit_info,
            language,
            profit=potential_profits["potential_profit"],
        )
        roi_line = loader.get(
            MessageKey.roi_info,
            language,
            roi=potential_profits["roi_percentage"],
        )

        lines.append(profit_line)
        lines.append(roi_line)

        # Add trading actions header
        lines.append("")
        lines.append(loader.get(MessageKey.trading_actions_header, language))

        # Add buy opportunities
        if trade_signals["buy_signals"]:
            lines.append(loader.get(MessageKey.buy_opportunities, language))
            for signal in trade_signals["buy_signals"]:
                date_str = signal["date"].strftime("%Y-%m-%d")
                date_line = loader.get(MessageKey.buy_date, language, date=date_str)
                lines.append(date_line)

        # Add sell opportunities
        if trade_signals["sell_signals"]:
            lines.append("")
            lines.append(loader.get(MessageKey.sell_opportunities, language))
            for signal in trade_signals["sell_signals"]:
                date_str = signal["date"].strftime("%Y-%m-%d")
                date_line = loader.get(MessageKey.sell_date, language, date=date_str)
                lines.append(date_line)

        return "\n".join(lines)

    def generate_trading_recommendations(
        self,
        forecast_data: np.ndarray,
        historical_data: pd.Series,
        forecast_dates: pd.DatetimeIndex,
        investment_amount: float,
    ) -> dict[str, Any]:
        """
        Generates comprehensive trading recommendations.

        Args:
            forecast_data: Forecasted stock prices
            historical_data: Historical stock price data
            forecast_dates: Dates corresponding to forecast data
            investment_amount: Amount to invest

        Returns:
            Dictionary with comprehensive trading recommendations
        """
        logger.info(
            f"Generating trading recommendations with investment amount: ${investment_amount:,.2f}"
        )

        # Identify optimal trades
        trade_signals = self.identify_optimal_trades(
            forecast_data, historical_data, forecast_dates
        )

        # Calculate potential profits based on signals
        potential_profits = self.calculate_potential_profits(
            trade_signals["buy_signals"],
            trade_signals["sell_signals"],
            investment_amount,
        )

        recommendations = {
            "trade_signals": trade_signals,
            "potential_profits": potential_profits,
            "investment_amount": investment_amount,
            "recommendation_summary": self._generate_recommendation_summary(
                trade_signals, potential_profits
            ),
        }

        logger.info("Trading recommendations generated successfully")
        return recommendations

    def calculate_potential_profits(
        self,
        buy_signals: list[dict],
        sell_signals: list[dict],
        investment_amount: float,
    ) -> dict[str, Any]:
        """
        Calculates potential profits from trading signals.

        Args:
            buy_signals: List of buy signals
            sell_signals: List of sell signals
            investment_amount: Amount to invest

        Returns:
            Dictionary with potential profit calculations
        """
        if not buy_signals or not sell_signals:
            return {
                "potential_profit": 0.0,
                "roi_percentage": 0.0,
                "trade_details": [],
                "max_theoretical_profit": 0.0,
            }

        # For simplicity, we'll simulate a basic trading strategy:
        # Buy at first buy signal, sell at first sell signal after that, repeat
        trade_details = []
        remaining_amount = investment_amount
        shares_owned = 0
        total_cost = 0

        buy_idx = 0
        sell_idx = 0

        while buy_idx < len(buy_signals) and sell_idx < len(sell_signals):
            # Find the next buy signal that comes before or at the same time as a sell signal
            buy_signal = buy_signals[buy_idx]
            sell_signal = sell_signals[sell_idx]

            if buy_signal["date"] < sell_signal["date"]:
                # Execute buy
                buy_price = buy_signal["price"]
                shares_to_buy = remaining_amount / buy_price
                shares_owned += shares_to_buy
                total_cost += remaining_amount
                remaining_amount = 0  # Use all available funds

                trade_details.append(
                    {
                        "action": "BUY",
                        "date": buy_signal["date"],
                        "price": buy_price,
                        "shares": shares_to_buy,
                        "amount_spent": remaining_amount,
                        "reason": buy_signal["reason"],
                    }
                )

                buy_idx += 1
            else:
                # Execute sell if we own shares
                if shares_owned > 0:
                    sell_price = sell_signal["price"]
                    revenue = shares_owned * sell_price
                    profit = revenue - total_cost
                    roi = (profit / total_cost) * 100 if total_cost > 0 else 0

                    trade_details.append(
                        {
                            "action": "SELL",
                            "date": sell_signal["date"],
                            "price": sell_price,
                            "shares": shares_owned,
                            "revenue": revenue,
                            "profit": profit,
                            "roi": roi,
                            "reason": sell_signal["reason"],
                        }
                    )

                    # Reset for next cycle
                    remaining_amount = revenue
                    shares_owned = 0
                    total_cost = 0

                sell_idx += 1

        # If we still own shares at the end, calculate potential profit if sold at last forecast price
        if shares_owned > 0:
            last_forecast_price = sell_signals[-1][
                "price"
            ]  # Use the last forecast price
            final_revenue = shares_owned * last_forecast_price
            final_profit = final_revenue - total_cost
            final_roi = (final_profit / total_cost) * 100 if total_cost > 0 else 0

            trade_details.append(
                {
                    "action": "SELL (simulated)",
                    "date": sell_signals[-1]["date"],
                    "price": last_forecast_price,
                    "shares": shares_owned,
                    "revenue": final_revenue,
                    "profit": final_profit,
                    "roi": final_roi,
                    "reason": "End of forecast period",
                }
            )

        # Calculate total potential profit
        total_profit = sum(
            trade["profit"] for trade in trade_details if "profit" in trade
        )

        # Calculate ROI
        roi_percentage = (
            (total_profit / investment_amount) * 100 if investment_amount > 0 else 0
        )

        # Calculate max theoretical profit (buy at lowest, sell at highest)
        if len(buy_signals) > 0 and len(sell_signals) > 0:
            min_buy_price = min([signal["price"] for signal in buy_signals])
            max_sell_price = max([signal["price"] for signal in sell_signals])
            if min_buy_price > 0:
                max_shares = investment_amount / min_buy_price
                max_theoretical_profit = max_shares * (max_sell_price - min_buy_price)
            else:
                max_theoretical_profit = 0.0
        else:
            max_theoretical_profit = 0.0

        return {
            "potential_profit": total_profit,
            "roi_percentage": roi_percentage,
            "trade_details": trade_details,
            "max_theoretical_profit": max_theoretical_profit,
            "total_trades_executed": len(
                [td for td in trade_details if td["action"] in ["BUY", "SELL"]]
            ),
        }

    def _generate_recommendation_summary(
        self, trade_signals: dict, potential_profits: dict
    ) -> str:
        """
        Generates a summary of the trading recommendations.

        Args:
            trade_signals: Trade signals dictionary
            potential_profits: Potential profits dictionary

        Returns:
            Recommendation summary string
        """
        if not trade_signals["buy_signals"] and not trade_signals["sell_signals"]:
            return "No clear trading opportunities identified. Market appears neutral in the forecast period."

        summary_parts = [
            f"Potential profit: ${potential_profits['potential_profit']:,.2f}",
            f"ROI: {potential_profits['roi_percentage']:.2f}%",
            f"Recommended actions: {trade_signals['strategy_summary']}",
        ]

        return " | ".join(summary_parts)

    def handle_no_clear_opportunity(self) -> dict[str, Any]:
        """
        Returns recommendations when no clear trading opportunity is identified.

        Returns:
            Dictionary with neutral recommendations
        """
        return {
            "trade_signals": {
                "buy_signals": [],
                "sell_signals": [],
                "total_buy_signals": 0,
                "total_sell_signals": 0,
                "strategy_summary": "No clear trading opportunities identified",
            },
            "potential_profits": {
                "potential_profit": 0.0,
                "roi_percentage": 0.0,
                "trade_details": [],
                "max_theoretical_profit": 0.0,
            },
            "investment_amount": 0.0,
            "recommendation_summary": "Market appears neutral. Consider holding position or dollar-cost averaging.",
        }
