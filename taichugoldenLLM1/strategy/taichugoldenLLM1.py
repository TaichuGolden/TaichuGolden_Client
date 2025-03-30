import json
class TaichuGoldenLLM1:
    def __init__(self, base):
        base.balance(cash=500000, leverage=10, fee_rate=0.00015, margin_rate=0.1)
        try:
            self.client = base.ws_client("ws://localhost:9000")
        except Exception as e:
            base.log(f"Error initializing TaichuGoldenLLM1: {e}")
            raise e
    async def on_tick(self, base):
        try:
            if len(base.data) <= 100:
                return
            df = base.data.copy(deep=True)
            df["macd"], df["macd_signal"], df["macd_hist"] = base.ind.macd_llm(df['CLOSE'], fast=12, slow=26, signal=9) 
           
            df["bollinger_upper"], df["bollinger_lower"], df["bollinger_middle"] = base.ind.bollinger_bands(df['CLOSE'], window=20, num_std=2) 
            
            df["rsi"] = base.ind.rsi(df['CLOSE'], window=14)

            df['time'] = df.index.astype(str)
            data_dict = df.to_dict(orient="records")
            prediction = await self.client.send_request(data_dict)
            prediction = base.json_load(prediction)['prediction']
            base.log(f"Prediction: {prediction}")
    
            if prediction-base.data['CLOSE'].iloc[-1] > 0:
                # base.close(side='SHORT', quantity_to_close=1, order_type='limit', 
                #            exit_price=base.data['CLOSE'].iloc[-1], send_msg=True, timestamp=base.data.index[-1], timeout='1d')
                base.open(side='LONG', quantity=1, order_type='limit', price=base.data['CLOSE'].iloc[-1], 
                          send_msg=True, timestamp=base.data.index[-1], timeout='1d', 
                          additional_params={'take_profit': base.data['CLOSE'].iloc[-1] * 1.02, 'stop_loss': base.data['CLOSE'].iloc[-1] * 0.98})

            elif prediction-base.data['CLOSE'].iloc[-1] < 0:
                # base.close(side='LONG', quantity_to_close=1, order_type='limit', 
                #            exit_price=base.data['CLOSE'].iloc[-1], send_msg=True, timestamp=base.data.index[-1], timeout='1d')
                base.open(side='SHORT', quantity=1, order_type='limit', price=base.data['CLOSE'].iloc[-1], 
                          send_msg=True, timestamp=base.data.index[-1], timeout='1d', 
                          additional_params={'take_profit': base.data['CLOSE'].iloc[-1] * 0.98, 'stop_loss': base.data['CLOSE'].iloc[-1] * 1.02})
            
            await self.client.send_request({"type": "end","data": base.end})
        except Exception as e:
            base.log(f"Error in on_tick: {e}")
            raise e
