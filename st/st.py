async def loop(base):
        def profit_positions(price_list,profit_levels):
            
            if len(profit_levels['LONG']['prices'])>0:
                if price_list[-1] >= profit_levels['LONG']['prices'][0]:
                    quant = profit_levels['LONG']['quantities'][0]
                    if base.long_amount and base.long_amount>0:
                        
                        base.close(
                            side='LONG',
                            quantity_to_close=quant,
                            exit_price=price_list[-1],
                            order_type='limit',
                            timestamp=base.data.index[-1],
                            timeout='1d',
                            additional_params=None
                        )
                        base.TrailingTakeProfit.update_profit_levels(isbuy=True,reset=False,condition=True)
                        # base.sell(size=quant,exectype=bt.Order.Market, price=profit_levels['LONG']['prices'][0],data=base.data,info={"order_type": "ProfitLong"})
        
            if len(profit_levels['SHORT']['prices'])>0:
                if price_list[-1] <= profit_levels['SHORT']['prices'][0]:
                    quant = profit_levels['SHORT']['quantities'][0]
                    if base.short_amount and base.short_amount>0:
                        
                        base.close(
                            side='SHORT',
                            quantity_to_close=quant,
                            exit_price=price_list[-1],
                            order_type='limit',
                            timestamp=base.data.index[-1],
                            timeout='1d',
                            additional_params=None
                        )
                        base.TrailingTakeProfit.update_profit_levels(isbuy=False,reset=False,condition=True)
                        # base.buy(size=quant,exectype=bt.Order.Market, price=profit_levels['SHORT']['prices'][0],data=base.data,info={"order_type": "ProfitShort"})
        
        if len(base.data) <= 720:
            print(f'no enough:{base.data.index[-1]},{len(base.data)}')
            return 
        ind = base.ind
        tools = base.tools
        p = base.p
        pricebymacdpr,trend_flag = ind.macd_divergence(base.data['CLOSE'],base.data['HIGH'],base.data['LOW'])
        atr_stop,atr             = ind.atr_stop(base.data['CLOSE'],base.data['HIGH'],base.data['LOW'],p.get('stoplossfactor',5))
        ema720                   = ind.calculate_ema(base.data['CLOSE'],p.get('emalongperiod',720))
        ema60                    = ind.calculate_ema(base.data['CLOSE'],p.get('emashortperiod',60))
        # try:
        #     base._write_to_db('atrstop',float(atr_stop[-1]),base.data.index[-1])
        #     base._write_to_db('ema60',float(ema60[-1]),base.data.index[-1])
        #     base._write_to_db('ema720',float(ema720[-1]),base.data.index[-1])
        #     base._write_to_db('pricebymacdpr',float(pricebymacdpr[-1]),base.data.index[-1])
        # except Exception as e:
        #     print(f"An error occurred in the _write_to_db function: {e}")
        # 开平仓条件
        long_condition = (atr_stop[-1] > atr_stop[-2]) and \
            (base.data['CLOSE'].iloc[-1] > pricebymacdpr[-1]) and \
            (base.data['CLOSE'].iloc[-1] > atr_stop[-1]) and \
            (trend_flag[-1] == 1 or trend_flag[-1] == 4)
        short_condition = (atr_stop[-1] < atr_stop[-2]) and \
            (base.data['CLOSE'].iloc[-1] < pricebymacdpr[-1]) and \
            (base.data['CLOSE'].iloc[-1] < atr_stop[-1]) and \
            (trend_flag[-1] == 2 or trend_flag[-1] == 3)
        close_long_condition  = (trend_flag[-1] == 2) or \
            (base.data['CLOSE'].iloc[-1] < atr_stop[-1]) or \
            ((trend_flag[-1] == 4) and (base.data['CLOSE'].iloc[-1] < pricebymacdpr[-1]))  
        close_short_condition = (trend_flag[-1] == 1) or \
            (base.data['CLOSE'].iloc[-1] > atr_stop[-1]) or \
            ((trend_flag[-1] == 3) and (base.data['CLOSE'].iloc[-1] > pricebymacdpr[-1]))  

        

        if not base.long_amount or base.long_amount == 0:
            base.TrailingTakeProfit.update_profit_levels(isbuy=True,reset=True,condition=True)
        if not base.short_amount or base.short_amount == 0:
            base.TrailingTakeProfit.update_profit_levels(isbuy=False,reset=True,condition=True)
        
        profit_positions(price_list=base.data['CLOSE'],profit_levels=base.TrailingTakeProfit.take_profit_levels)
        # print('base.TrailingTakeProfit.take_profit_levels:',base.TrailingTakeProfit.take_profit_levels)
        # print('long_price:',base.long_price)
        # print('long_amount:',base.long_amount)
        # print('short_amount:',base.short_amount)
        # print('short_price:',base.short_price)
        if close_long_condition and base.long_amount and base.long_amount>0:
            
            base.close(
                side='LONG',
                quantity_to_close=base.long_amount,
                exit_price=base.data['CLOSE'].iloc[-1],
                order_type='limit',
                timestamp=base.data.index[-1],
                timeout='1d',
                additional_params=None
            )
        if close_short_condition and base.short_amount and base.short_amount>0:
            
            base.close(
                side='SHORT',
                quantity_to_close=base.short_amount,
                exit_price=base.data['CLOSE'].iloc[-1],
                order_type='limit',
                timestamp=base.data.index[-1],
                timeout='1d',
                additional_params=None
            )
        base.PyramidPositionSizer.update_trade_counts(isbuy=True,condition=(base.long_amount==0 or not base.long_amount))   # 重置
        base.PyramidPositionSizer.update_trade_counts(isbuy=False,condition=(base.short_amount==0 or not base.short_amount)) # 重置
        # 开仓执行,先计算开仓数量
        size_short,info_short = base.PyramidPositionSizer.getsize(cash=base.cash*base.leverage, atr=atr[-1], isbuy=False,condition=short_condition)
        size_long,info_long = base.PyramidPositionSizer.getsize(cash=base.cash*base.leverage, atr=atr[-1], isbuy=True,condition=long_condition)
        
        if size_long:
            base.open(
                side='LONG',
                quantity=size_long,
                order_type='limit',
                price=base.data['CLOSE'].iloc[-1],
                send_msg=True,
                timestamp=base.data.index[-1],
                timeout='1d',
                additional_params=None
            )
        if size_short:
            base.open(
                side='SHORT',
                quantity=size_short,
                order_type='limit',
                price=base.data['CLOSE'].iloc[-1],
                send_msg=True,
                timestamp=base.data.index[-1],
                timeout='1d',
                additional_params=None
            )
        if base.long_amount and base.long_amount>0:
            base.TrailingTakeProfit.calculate_profit_levels(
                isbuy=True,
                position_quantity=base.long_amount,
                average_price=base.long_price,
                stop_loss_price=atr_stop[-1],
                latest_close_price=base.data['CLOSE'].iloc[-1],
                condition=(base.long_amount != 0)
            )
        if base.short_amount and base.short_amount>0:
            base.TrailingTakeProfit.calculate_profit_levels(
                isbuy=False,
                position_quantity=base.short_amount,
                average_price=base.short_price,
                stop_loss_price=atr_stop[-1],
                latest_close_price=base.data['CLOSE'].iloc[-1],
                condition=(base.short_amount != 0)
            )
        