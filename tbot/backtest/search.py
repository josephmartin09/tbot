class Search:
    """Class to search a CandleSeries for profitable buying and selling opportunities."""

    def __init__(self, candles):
        """Initialize the Search object.

        :param CandleSeries candles: The candle series to use as search data
        """
        self._candles = candles

    def profitable_candles(self, profit_target, reward_risk_ratio=2.0):
        """Return a list of profitable candles based on configured reward/risk ratio.

        :param int profit_target: The number of points to attempt to target
        :param float reward_risk_ratio: The reward/risk ratio to use in determing if a candle is profitable

        .. note::
            1) This function assumes an order is filled at the open price of a candle
            2) This function assumes that if the candle hits both the stop loss and the target, the stop loss is hit before the target

        """
        # Search for buys
        buys = []
        for i in range(len(self._candles)):
            entry_candle = self._candles[i]
            entry_price = entry_candle.open

            target = entry_price + profit_target
            sl = entry_price - (profit_target / reward_risk_ratio)

            profit = False
            for j in range(i, len(self._candles)):
                future_candle = self._candles[j]
                if future_candle.low <= sl:
                    break
                elif future_candle.high >= target:
                    profit = True
                    break
            if profit:
                buys.append(entry_candle)

        # Search for sells
        sells = []
        for i in range(len(self._candles)):
            entry_candle = self._candles[i]
            entry_price = entry_candle.open

            target = entry_price - profit_target
            sl = entry_price + (profit_target / reward_risk_ratio)

            profit = False
            for j in range(i, len(self._candles)):
                future_candle = self._candles[j]
                if future_candle.high >= sl:
                    break
                elif future_candle.high <= target:
                    profit = True
                    break
            if profit:
                sells.append(entry_candle)

        return {"buys": buys, "sells": sells}
