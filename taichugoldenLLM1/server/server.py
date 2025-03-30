from taichu_websocket import WebSocketServer
import json
# from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import joblib
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
# scaler_path = 'D:/AutoTrading/backtrader/system/transformer_predict/scaler.pkl'
model_path = 'D:/AutoTrading/backtrader/system/transformer_predict/transformer_ohlcv_model_for_return_optimized.h5'
model = tf.keras.models.load_model(model_path)
def rolling_normalization(data, window=60):
    """
    对数据进行滚动窗口归一化，避免未来数据影响当前数据。
    :param data: 输入的时间序列数据，pandas DataFrame 或 Series
    :param window: 滚动窗口的大小，默认60
    :return: 归一化后的数据
    """
    rolling_min = data.rolling(window=window, min_periods=1).min()
    rolling_max = data.rolling(window=window, min_periods=1).max()
    normalized_data = (data - rolling_min) / (rolling_max - rolling_min)
    return normalized_data

def rolling_normalization_multifeature(data, window=60):
    """
    对多个特征进行滚动窗口归一化
    :param data: 包含多个特征的 DataFrame
    :param window: 滚动窗口的大小，默认60
    :return: 归一化后的 DataFrame
    """
    normalized_data = data.copy()
    for column in data.columns:
        normalized_data[column] = rolling_normalization(data[column], window)
        normalized_data.dropna(inplace=True)
    # print(normalized_data)
    return normalized_data

def sliding_window_predict(df, look_back=10):
    # if not os.path.exists(scaler_path):
    #     X_new, scaler = prepare_new_data(df, look_back, scaler=None)
    # else:
    #     scaler = joblib.load(scaler_path)
    #     X_new, _ = prepare_new_data(df, look_back, scaler)
    X_new, scaler = prepare_new_data(df, look_back, scaler=None)
    if len(X_new) == 0:
        raise ValueError("Not enough data for prediction")

    # # **修改点**：保持数据形状符合 Transformer 模型要求
    # X_input = X_new[-1:].reshape(1, look_back, -1)  # (1, 5, 10)

    # prediction = model.predict(X_input)[0][0]

    # # 只对最后一个特征值进行逆变换
    # prediction = scaler.inverse_transform(
    #     [[0] * (X_new.shape[-1] - 1) + [prediction]]
    # )[0][-1]

    # return prediction
    # 进行预测
    X_input = X_new[-1:].reshape(1, look_back, -1)  # (1, 5, 10)
    # print(X_input.shape)
    predicted_return = model.predict(X_input)[0][0]

    # 将预测的收益率转换为价格变化
    last_close_price = df['CLOSE'].iloc[-1]
    predicted_price = last_close_price * (1 + predicted_return)

    print(f'Predicted Return: {predicted_return:.6f}')
    print(f'Predicted Price: {predicted_price:.2f}')
    return predicted_price

def prepare_new_data(df, look_back=10, scaler=None):
    df = df.dropna()  
    features = ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOL', 'rsi', 'macd', 'macd_signal', 'macd_hist', 'bollinger_middle']
    # X = []
    # X = np.lib.stride_tricks.sliding_window_view(df[features].values, (look_back, df[features].shape[1]))
    # if scaler is None:
    #     scaler = MinMaxScaler()
    #     X = scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
    #     joblib.dump(scaler, scaler_path) 
    # else:
    #     X = scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
    # return X, scaler
    # 归一化
    data = rolling_normalization_multifeature(df[features], window=60)
    X = np.lib.stride_tricks.sliding_window_view(data[features].values, (look_back, data[features].shape[1]))
    # # 取最近 look_back 个时间步的数据
    # X_pred = data.iloc[-look_back:].values
    # X_pred = np.expand_dims(X_pred, axis=0)  # 增加批次维度，使其符合模型输入形状 (1, look_back, feature_dim)
    return X, scaler
            
async def TaichuGoldenLLM1(data, websocket):
    if type(data) == dict and data.get('type') == 'end':
        if data.get('data') == 1:
            plot_comparison()
        await websocket.send(json.dumps({"end": True}))    
        return
    
    df = pd.DataFrame(data)
    prediction = sliding_window_predict(df, look_back=10)
    print(f"Prediction: {prediction}")
    await websocket.send(json.dumps({"prediction": prediction}))

    global history_df  # 访问全局变量
    df["time"] = pd.to_datetime(df["time"])
    new_data = pd.DataFrame({
        "time": df["time"].iloc[-1:],  # 取最新时间点
        "actual": df["CLOSE"].iloc[-1:],  # 取最新实际值
        "predicted": [prediction]  # 预测值
    })
    history_df = pd.concat([history_df, new_data], ignore_index=True)
    # plot_comparison()
def plot_comparison():
    if history_df.empty:
        return

    plt.figure(figsize=(10, 5))
    plt.plot(history_df["time"], history_df["actual"], label="Actual", marker="o")
    plt.plot(history_df["time"], history_df["predicted"], label="Predicted", marker="s")

    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title("Actual vs Predicted")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()
    statistics(history_df)
def statistics(df):
    history_df = df.copy(deep=True)
    # 计算 a：下一行 actual 减去当前行 actual
    history_df["a"] = history_df["actual"].shift(-1) - history_df["actual"]

    # 计算 b：predicted - actual
    history_df["b"] = history_df["predicted"] - history_df["actual"]

    # 判断 a 是否大于 0，赋值为 1 或 0
    history_df["a_flag"] = (history_df["a"] > 0).astype(int)

    # 判断 b 是否大于 0，赋值为 1 或 0
    history_df["b_flag"] = (history_df["b"] > 0).astype(int)

    # 判断 a 和 b 是否同向
    history_df["same_direction"] = (history_df["a_flag"] == history_df["b_flag"]).astype(int)

    # 统计同向和不同向的次数
    same_direction_count = history_df["same_direction"].sum()
    different_direction_count = len(history_df) - same_direction_count

    # 计算准确率
    accuracy = same_direction_count / (same_direction_count + different_direction_count)

    # 打印结果
    print(f"Right: {same_direction_count}")
    print(f"Wrong: {different_direction_count}")
    print(f"Accuracy: {accuracy:.2%}")
history_df = pd.DataFrame(columns=["time", "actual", "predicted"])
server = WebSocketServer(host="0.0.0.0", port=9000)
server.set_handler(TaichuGoldenLLM1)
server.run()