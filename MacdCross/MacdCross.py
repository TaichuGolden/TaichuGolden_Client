class MacdCross:
    def __init__(self, base):
        base.balance(cash=500000, leverage=10, fee_rate=0.00015, margin_rate=0.1)

    async def on_tick(self, base):
        try:
            if len(base.data) <= 100:
                return
            
            macd, signal, hist = base.ind.macd(
                data=base.data['CLOSE'], 
                fastperiod=12, 
                slowperiod=26, 
                signalperiod=9
            )
            cross = base.tools.cross(macd, signal)
            last_price = base.data['CLOSE'].iloc[-1]
            timestamp = base.data.index[-1]

            # 交易条件优化
            if cross > 0 and hist.iloc[-1] > 0:
                base.close(side='SHORT', quantity_to_close=1, order_type='limit', 
                           exit_price=last_price, send_msg=True, timestamp=timestamp, timeout='1d')
                base.open(side='LONG', quantity=1, order_type='limit', price=last_price, 
                          send_msg=True, timestamp=timestamp, timeout='1d', 
                          additional_params={'take_profit': last_price * 1.02, 'stop_loss': last_price * 0.98})

            elif cross < 0 and hist.iloc[-1] < 0:
                base.close(side='LONG', quantity_to_close=1, order_type='limit', 
                           exit_price=last_price, send_msg=True, timestamp=timestamp, timeout='1d')
                base.open(side='SHORT', quantity=1, order_type='limit', price=last_price, 
                          send_msg=True, timestamp=timestamp, timeout='1d', 
                          additional_params={'take_profit': last_price * 0.98, 'stop_loss': last_price * 1.02})

        except Exception as e:
            print(f"Error in on_tick: {e}")
