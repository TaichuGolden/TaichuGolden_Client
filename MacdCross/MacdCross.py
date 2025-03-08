
class MacdCross:
    def __init__(self,base):
        base.balance(cash=500000,leverage=10,fee_rate=0.00015,margin_rate=0.1)
    async def on_tick(self,base):
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
            if cross > 0:
                base.close(
                    side='SHORT',
                    quantity_to_close=1,
                    order_type='limit',
                    exit_price=base.data['CLOSE'].iloc[-1],
                    send_msg=True,
                    timestamp=base.data.index[-1],
                    timeout='1d',
                    additional_params=None
                )
                base.open(
                    side='LONG',
                    quantity=1,
                    order_type='limit',
                    price=base.data['CLOSE'].iloc[-1],
                    send_msg=True,
                    timestamp=base.data.index[-1],
                    timeout='1d',
                    additional_params=None
                )
            if cross < 0:
                base.close(
                    side='LONG',
                    quantity_to_close=1,
                    order_type='limit',
                    exit_price=base.data['CLOSE'].iloc[-1],
                    send_msg=True,
                    timestamp=base.data.index[-1],
                    timeout='1d',
                    additional_params=None
                )
                base.open(
                    side='SHORT',
                    quantity=1,
                    order_type='limit',
                    price=base.data['CLOSE'].iloc[-1],
                    send_msg=True,
                    timestamp=base.data.index[-1],
                    timeout='1d',
                    additional_params=None
                )
        except Exception as e:
            raise e
