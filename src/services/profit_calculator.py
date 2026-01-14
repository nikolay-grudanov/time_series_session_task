"""
Service for calculating potential profit.
"""
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ProfitCalculatorService:
    """
    Service for calculating potential profit based on investment amount and trading strategy.
    """
    def __init__(self):
        pass

    def calculate_profit_from_trades(
        self,
        trade_signals: list[dict],
        investment_amount: float,
        initial_price: float
    ) -> dict[str, Any]:
        """
        Calculates profit based on trading signals and investment amount.

        Args:
            trade_signals: List of buy/sell signals
            investment_amount: Initial investment amount
            initial_price: Price at the beginning of the period

        Returns:
            Dictionary with profit calculations
        """
        logger.info(f"Calculating profit for investment amount: ${investment_amount:,.2f}")

        # Track portfolio state
        cash = investment_amount
        shares = 0
        transactions = []

        # Execute trades based on signals
        for signal in trade_signals:
            date = signal['date']
            price = signal['price']
            reason = signal['reason']

            if signal['action'] == 'BUY':
                # Calculate how many shares to buy
                shares_to_buy = cash / price
                shares += shares_to_buy
                cash = 0  # Use all available cash

                transaction = {
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares_to_buy,
                    'cash_flow': -shares_to_buy * price,  # Negative cash flow for purchase
                    'cash_after': cash,
                    'portfolio_value': shares * price,
                    'reason': reason
                }

                transactions.append(transaction)

            elif signal['action'] == 'SELL':
                # Sell all shares
                cash_from_sale = shares * price
                cash += cash_from_sale
                shares = 0  # Sell all shares

                transaction = {
                    'date': date,
                    'action': 'SELL',
                    'price': price,
                    'shares': -shares,  # Negative indicates sale
                    'cash_flow': cash_from_sale,  # Positive cash flow for sale
                    'cash_after': cash,
                    'portfolio_value': cash,
                    'reason': reason
                }

                transactions.append(transaction)

        # Calculate final portfolio value (if we still hold shares)
        final_portfolio_value = cash + (shares * initial_price if shares > 0 else 0)

        # Calculate profit
        profit = final_portfolio_value - investment_amount
        roi = (profit / investment_amount) * 100 if investment_amount > 0 else 0

        # Calculate profit metrics
        results = {
            'initial_investment': investment_amount,
            'final_portfolio_value': final_portfolio_value,
            'profit': profit,
            'roi_percentage': roi,
            'transactions': transactions,
            'total_transactions': len(transactions),
            'net_cash_flow': sum(t['cash_flow'] for t in transactions)
        }

        logger.info(f"Profit calculation completed. Profit: ${profit:,.2f}, ROI: {roi:.2f}%")
        return results

    def calculate_detailed_profit_analysis(
        self,
        buy_signals: list[dict],
        sell_signals: list[dict],
        investment_amount: float,
        initial_price: float,
        final_price: float
    ) -> dict[str, Any]:
        """
        Performs a detailed profit analysis considering both buy/sell signals and holding strategy.

        Args:
            buy_signals: List of buy signals
            sell_signals: List of sell signals
            investment_amount: Initial investment amount
            initial_price: Price at the beginning of the period
            final_price: Price at the end of the period

        Returns:
            Dictionary with detailed profit analysis
        """
        logger.info("Performing detailed profit analysis")

        # Calculate profit from trading strategy
        all_signals = []

        # Combine buy and sell signals, keeping track of action type
        for signal in buy_signals:
            all_signals.append({**signal, 'action': 'BUY'})

        for signal in sell_signals:
            all_signals.append({**signal, 'action': 'SELL'})

        # Sort signals by date
        all_signals.sort(key=lambda x: x['date'])

        # Calculate profit from active trading
        trading_results = self.calculate_profit_from_trades(
            all_signals,
            investment_amount,
            final_price
        )

        # Calculate profit from holding strategy (buy at start, sell at end)
        if initial_price > 0:
            shares_bought = investment_amount / initial_price
            holding_profit = (shares_bought * final_price) - investment_amount
            holding_roi = (holding_profit / investment_amount) * 100 if investment_amount > 0 else 0
        else:
            holding_profit = 0
            holding_roi = 0

        # Calculate benchmark profit (if we had perfect foresight - buy at lowest, sell at highest)
        all_prices = [s['price'] for s in all_signals if s['price'] > 0]
        if all_prices:
            min_price = min(all_prices)
            max_price = max(all_prices)

            if min_price > 0:
                max_shares = investment_amount / min_price
                benchmark_profit = (max_shares * max_price) - investment_amount
                benchmark_roi = (benchmark_profit / investment_amount) * 100 if investment_amount > 0 else 0
            else:
                benchmark_profit = 0
                benchmark_roi = 0
        else:
            benchmark_profit = 0
            benchmark_roi = 0

        # Calculate risk metrics
        price_volatility = np.std(all_prices) if all_prices else 0
        max_drawdown = self._calculate_max_drawdown(all_signals, investment_amount) if all_signals else 0

        # Compile detailed analysis
        analysis = {
            'trading_strategy': trading_results,
            'holding_strategy': {
                'profit': holding_profit,
                'roi_percentage': holding_roi
            },
            'benchmark_strategy': {
                'profit': benchmark_profit,
                'roi_percentage': benchmark_roi
            },
            'comparison': {
                'active_vs_hold': trading_results['profit'] - holding_profit,
                'active_vs_benchmark': trading_results['profit'] - benchmark_profit,
                'hold_vs_benchmark': holding_profit - benchmark_profit
            },
            'risk_metrics': {
                'price_volatility': price_volatility,
                'max_drawdown': max_drawdown
            },
            'effectiveness': self._calculate_strategy_effectiveness(trading_results['roi_percentage'], holding_roi)
        }

        logger.info("Detailed profit analysis completed")
        return analysis

    def _calculate_max_drawdown(self, signals: list[dict], initial_capital: float) -> float:
        """
        Calculates the maximum drawdown of the trading strategy.

        Args:
            signals: List of trading signals
            initial_capital: Initial capital amount

        Returns:
            Maximum drawdown as a percentage
        """
        if not signals:
            return 0.0

        # Track portfolio value over time
        portfolio_values = [initial_capital]
        cash = initial_capital
        shares = 0

        # Go through each signal and update portfolio value
        for i in range(len(signals)):
            signal = signals[i]
            price = signal['price']

            if signal['action'] == 'BUY':
                # Convert cash to shares
                shares += cash / price
                cash = 0
            elif signal['action'] == 'SELL':
                # Convert shares to cash
                cash += shares * price
                shares = 0

            # Portfolio value is cash + value of shares at current price
            current_value = cash + (shares * price)
            portfolio_values.append(current_value)

        # Calculate max drawdown
        peak = float('-inf')
        max_dd = 0

        for value in portfolio_values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak != 0 else 0
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_strategy_effectiveness(self, trading_roi: float, holding_roi: float) -> str:
        """
        Determines how effective the trading strategy was compared to holding.

        Args:
            trading_roi: ROI of the trading strategy
            holding_roi: ROI of the holding strategy

        Returns:
            Effectiveness rating
        """
        if trading_roi > holding_roi + 2:  # Significantly outperforms holding
            return "Highly Effective"
        elif trading_roi > holding_roi:  # Slightly outperforms holding
            return "Moderately Effective"
        elif trading_roi > holding_roi - 2:  # Nearly matches holding
            return "Marginally Effective"
        else:  # Underperforms holding
            return "Ineffective"

    def calculate_scenario_analysis(
        self,
        forecast_data: np.ndarray,
        investment_amount: float,
        initial_price: float
    ) -> dict[str, Any]:
        """
        Calculates profit under different market scenarios.

        Args:
            forecast_data: Forecasted price data
            investment_amount: Initial investment amount
            initial_price: Initial price

        Returns:
            Dictionary with scenario analysis
        """
        logger.info("Calculating scenario analysis")

        if len(forecast_data) == 0:
            return {
                'best_case': {'profit': 0, 'roi': 0},
                'worst_case': {'profit': 0, 'roi': 0},
                'average_case': {'profit': 0, 'roi': 0}
            }

        # Best case: buy at minimum price, sell at maximum price
        min_price = min(forecast_data)
        max_price = max(forecast_data)

        if min_price > 0:
            shares_at_min = investment_amount / min_price
            best_case_profit = (shares_at_min * max_price) - investment_amount
            best_case_roi = (best_case_profit / investment_amount) * 100 if investment_amount > 0 else 0
        else:
            best_case_profit = 0
            best_case_roi = 0

        # Worst case: buy at maximum price, sell at minimum price
        if max_price > 0:
            shares_at_max = investment_amount / max_price
            worst_case_profit = (shares_at_max * min_price) - investment_amount
            worst_case_roi = (worst_case_profit / investment_amount) * 100 if investment_amount > 0 else 0
        else:
            worst_case_profit = 0
            worst_case_roi = 0

        # Average case: use average price
        avg_price = np.mean(forecast_data)
        if initial_price > 0:
            shares_initial = investment_amount / initial_price
            avg_case_profit = (shares_initial * avg_price) - investment_amount
            avg_case_roi = (avg_case_profit / investment_amount) * 100 if investment_amount > 0 else 0
        else:
            avg_case_profit = 0
            avg_case_roi = 0

        scenarios = {
            'best_case': {
                'profit': best_case_profit,
                'roi': best_case_roi,
                'description': f"Buy at lowest forecast price (${min_price:.2f}), sell at highest (${max_price:.2f})"
            },
            'worst_case': {
                'profit': worst_case_profit,
                'roi': worst_case_roi,
                'description': f"Buy at highest forecast price (${max_price:.2f}), sell at lowest (${min_price:.2f})"
            },
            'average_case': {
                'profit': avg_case_profit,
                'roi': avg_case_roi,
                'description': f"Using average forecast price (${avg_price:.2f})"
            }
        }

        logger.info("Scenario analysis completed")
        return scenarios
