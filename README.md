# 📈 EURUSD Algorithmic Trading Bot

**Course:** Integrating Aspects of Asset Management  
**Date:** January 2026  

### 👥 Team Members
* **Tayebeh Oveisi Fardoye**
* **Sara Eghlidi**
* **Alejandro Arzola de Leon**
* **Hadi Shahparvari**

---

## 📝 Project Overview
This project implements a fully automated algorithmic trading system for the **EURUSD** forex pair. It consists of two main parts:

1.  **Data Mining & Backtesting:** We analyzed 1 year of 1-minute historical data (Nov 2024 - Oct 2025) to test 5 distinct strategies (SMA, Momentum, RSI, Mean Reversion, Breakout).
2.  **Live Server Deployment:** We deployed the strategies to a Linux server connected to Interactive Brokers (IB Gateway).

### 🚀 Bonus Feature: Adaptive Regime Switching
To address performance decay seen in Out-of-Sample testing, we created an enhanced bot (**`main_adaptive.py`**).
* **The Problem:** The standard Momentum strategy fails during choppy (sideways) markets.
* **The Solution:** We implemented a "Regime Switching" algorithm.
* **How it works:** The bot calculates the **Rolling Sharpe Ratio** in real-time.
    * If `Sharpe > 0`: It trades **Momentum**.
    * If `Sharpe < 0`: It switches to **Mean Reversion**.

---

## 📂 File Structure

### 📘 Documentation & Analysis
| File Name | Description |
| :--- | :--- |
| **`Assignment_Final.ipynb`** | The complete Jupyter Notebook. Includes data mining, backtesting results, and the **Bonus** mathematical proof. |
| **`Project_Report.pdf`** | The final PDF report detailing our methodology and conclusion. |
| **`EURUSD_1min_data.csv`** | The historical data used for Part 1 analysis. |

### 🤖 Trading Bots (Source Code)
| File Name | Description |
| :--- | :--- |
| **`main.py`** | **(Standard)** The basic Momentum Bot required for the assignment. |
| **`main_adaptive.py`** | **(Bonus)** The advanced bot with Regime Switching (Momentum ↔ Mean Reversion). |

### ⚙️ Server Configuration & Proof
| File Name | Description |
| :--- | :--- |
| **`algo.service`** | Systemd configuration file to run the bot as a background process on Linux. |
| **`Picture of Server Part.pdf`** | **Proof 1:** Screenshot showing the standard `main.py` running successfully. |
| **`Picture of server for suggestion part.pdf`** | **Proof 2:** Screenshot showing the `main_adaptive.py` running with the connection retry loop working. |

---

## ⚙️ Installation & Deployment

The bot is designed to run on a Linux server (Ubuntu/Debian) with **Interactive Brokers Gateway**.

### 1. Setup (Linux)
```bash
# 1. Clone the repository
git clone [https://github.com/YourUsername/YourRepoName.git](https://github.com/YourUsername/YourRepoName.git)
cd YourRepoName

# 2. Move files to the deployment folder
mkdir -p /home/paper_algo
cp main_adaptive.py /home/paper_algo/

# 3. Configure the Service
sudo cp algo.service /etc/systemd/system/
sudo systemctl daemon-reload
