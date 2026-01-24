# EURUSD Algorithmic Trading Project 📈

**Course:** Integrating Aspects of Asset Management                                                                                               
**Strategy:** Momentum (10-minute Lookback)  
**Status:** Completed ✅

## 📌 Project Overview
This project performs data mining on 1-year of high-frequency EURUSD data (Nov 2024 - Oct 2025) to identify profitable trading strategies. The winning strategy was backtested, validated out-of-sample, and deployed as a live trading bot on a Linux server.

## 📂 File Structure
* **`Assignment_Final.ipynb`**: The main research notebook. Contains data mining of 5 strategies, backtesting, and visualization.
* **`EURUSD_1min_data.csv`**: 1-minute OHLC market data used for the analysis.
* **`main.py`**: The Python script for the live trading bot (connects to IB Gateway).
* **`algo.service`**: Systemd configuration for running the bot as a background service.

## 🚀 How to Run the Code
1. **Research (Notebook):**
   * Download `Assignment_Final.ipynb` and `EURUSD_1min_data.csv`.
   * Ensure both files are in the same folder.
   * Run the notebook using Jupyter Lab or VS Code.

2. **Server (Bot):**
   * The `main.py` requires `ib_async` and a running instance of IB Gateway (Port 4002).
   * It is configured to trade the "Momentum" strategy (Buy when 10-min trend is positive).

## 📊 Results
* **Winning Strategy:** Momentum
* **In-Sample Sharpe (Training):** 5.08 (Rank 1)
* **Out-of-Sample Result:** -8.68% (Demonstrating market regime change/overfitting).
