async def loop(base):
    try:
        if len(base.data) <= 100:
            return 
        ind = base.ind
        tools = base.tools
        macd, signal, hist = ind.macd(
            data=base.data['CLOSE'], 
            fastperiod=12, 
            slowperiod=26, 
            signalperiod=9
            ) 
        cross = tools.cross(macd, signal)
        if cross > 0:
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
