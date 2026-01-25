#!/usr/bin/env python3
"""
EURUSD ADAPTIVE Trading Bot - Enhanced Version
===============================================
Team: Tayebeh Oveisi Fardoye, Sara Eghlidi, Alejandro Arzola de Leon, Hadi Shahparvari

This bot monitors performance and automatically switches strategies
when the current strategy underperforms.

Strategies (in order):
1. Momentum
2. Breakout  
3. RSI_Trend
4. Mean_Reversion
5. SMA_Crossover
"""

from ib_insync import IB, Forex, MarketOrder
import datetime
import time
import logging
import numpy as np
from collections import deque

# === CONFIGURATION ===
SYMBOL = 'EURUSD'
POSITION_SIZE = 20000
IB_HOST = '127.0.0.1'
IB_PORT = 4002
CLIENT_ID = 1

# Adaptive Parameters
LOOKBACK_BARS = 7200  # 5 days of 1-min bars
SHARPE_THRESHOLD = 0  # Switch if Sharpe drops below 0
MIN_SWITCH_INTERVAL = 1440  # Minimum 1 day between switches

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('adaptive_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === GLOBAL VARIABLES ===
ib = IB()
contract = Forex(SYMBOL)

# Strategy Management
strategy_order = ['Momentum', 'Breakout', 'RSI_Trend', 'Mean_Reversion', 'SMA_Crossover']
current_strategy = 'Momentum'
last_switch_time = None

# Performance Tracking
prices_history = deque(maxlen=100)
returns_history = deque(maxlen=LOOKBACK_BARS)
last_signal = 0


# === STRATEGY FUNCTIONS ===

def get_momentum_signal(prices):
    """Momentum: Buy if price > price 10 bars ago"""
    if len(prices) < 11:
        return 0
    return 1 if prices[-1] > prices[-11] else -1


def get_breakout_signal(prices):
    """Breakout: Buy if price >= 20-bar high"""
    if len(prices) < 20:
        return 0
    return 1 if prices[-1] >= max(prices[-20:]) else -1


def get_rsi_signal(prices):
    """RSI: Buy if RSI > 50"""
    if len(prices) < 15:
        return 0
    deltas = np.diff(list(prices)[-15:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0
    if avg_loss == 0:
        return 1
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return 1 if rsi > 50 else -1


def get_mean_reversion_signal(prices):
    """Mean Reversion: Sell if price > SMA, Buy if price < SMA"""
    if len(prices) < 50:
        return 0
    sma = np.mean(list(prices)[-50:])
    return -1 if prices[-1] > sma else 1


def get_sma_crossover_signal(prices):
    """SMA Crossover: Buy if price > SMA"""
    if len(prices) < 50:
        return 0
    sma = np.mean(list(prices)[-50:])
    return 1 if prices[-1] > sma else -1


def get_signal(strategy_name, prices):
    """Get signal from specified strategy"""
    if strategy_name == 'Momentum':
        return get_momentum_signal(prices)
    elif strategy_name == 'Breakout':
        return get_breakout_signal(prices)
    elif strategy_name == 'RSI_Trend':
        return get_rsi_signal(prices)
    elif strategy_name == 'Mean_Reversion':
        return get_mean_reversion_signal(prices)
    elif strategy_name == 'SMA_Crossover':
        return get_sma_crossover_signal(prices)
    return 0


# === PERFORMANCE MONITORING ===

def calculate_rolling_sharpe():
    """Calculate rolling Sharpe ratio"""
    if len(returns_history) < 1000:
        return 999  # Not enough data, don't switch
    returns = np.array(returns_history)
    if np.std(returns) == 0:
        return 0
    return (np.mean(returns) / np.std(returns)) * np.sqrt(252 * 1440)


def should_switch_strategy():
    """Check if we should switch to next strategy"""
    global last_switch_time
    
    now = datetime.datetime.now()
    
    # Don't switch too frequently
    if last_switch_time:
        minutes_since = (now - last_switch_time).total_seconds() / 60
        if minutes_since < MIN_SWITCH_INTERVAL:
            return False, "Too soon"
    
    # Check Sharpe
    rolling_sharpe = calculate_rolling_sharpe()
    
    if rolling_sharpe < SHARPE_THRESHOLD:
        return True, f"Sharpe ({rolling_sharpe:.2f}) < {SHARPE_THRESHOLD}"
    
    return False, f"OK (Sharpe: {rolling_sharpe:.2f})"


def switch_to_next_strategy():
    """Switch to next strategy in order"""
    global current_strategy, last_switch_time
    
    current_idx = strategy_order.index(current_strategy)
    next_idx = (current_idx + 1) % len(strategy_order)
    
    old_strategy = current_strategy
    current_strategy = strategy_order[next_idx]
    last_switch_time = datetime.datetime.now()
    
    logger.warning(f"SWITCH: {old_strategy} -> {current_strategy}")
    
    return current_strategy


# === TRADING LOGIC ===

def get_current_position():
    """Get current EUR position"""
    positions = ib.positions()
    for p in positions:
        if p.contract.symbol == 'EUR':
            return p.position
    return 0


def on_bar_update(bars, hasNewBar):
    """Main callback - runs on each new bar"""
    global last_signal
    
    if not hasNewBar or len(bars) < 11:
        return
    
    try:
        # Update price history
        current_price = bars[-1].close
        prices_history.append(current_price)
        
        # Calculate return
        if len(prices_history) > 1:
            ret = (prices_history[-1] - prices_history[-2]) / prices_history[-2]
            strategy_return = last_signal * ret
            returns_history.append(strategy_return)
        
        # Check if should switch strategy
        should_switch, reason = should_switch_strategy()
        if should_switch:
            switch_to_next_strategy()
            logger.warning(f"   Reason: {reason}")
        
        # Get signal from current strategy
        prices_list = list(prices_history)
        signal = get_signal(current_strategy, prices_list)
        last_signal = signal
        
        # Get position
        current_pos = get_current_position()
        
        # Log status
        sharpe = calculate_rolling_sharpe()
        logger.info(f"[{current_strategy}] Price: {current_price:.5f} | Signal: {signal} | Sharpe: {sharpe:.2f}")
        
        # Execute trades
        if signal > 0 and current_pos <= 0:
            ib.placeOrder(contract, MarketOrder('BUY', POSITION_SIZE))
            logger.info(f"BUY ({current_strategy})")
            
        elif signal < 0 and current_pos >= 0:
            ib.placeOrder(contract, MarketOrder('SELL', POSITION_SIZE))
            logger.info(f"SELL ({current_strategy})")
            
    except Exception as e:
        logger.error(f"Error: {e}")


# === TRADING HOURS ===

def is_trading_hours():
    """Check if within forex trading hours"""
    now = datetime.datetime.now()
    weekday = now.weekday()
    hour = now.hour
    
    if weekday == 5:  # Saturday
        return False
    if weekday == 6 and hour < 17:  # Sunday before 5pm
        return False
    if weekday == 4 and hour >= 17:  # Friday after 5pm
        return False
    return True


# === MAIN LOOP ===

def main():
    """Main trading loop"""
    logger.info("=" * 60)
    logger.info("ADAPTIVE EURUSD TRADING BOT STARTED")
    logger.info(f"   Initial Strategy: {current_strategy}")
    logger.info(f"   Sharpe Threshold: {SHARPE_THRESHOLD}")
    logger.info(f"   Strategy Order: {' -> '.join(strategy_order)}")
    logger.info("=" * 60)
    
    bars = None
    
    while True:
        try:
            if is_trading_hours():
                if not ib.isConnected():
                    logger.info("Trading hours - Connecting...")
                    ib.connect(IB_HOST, IB_PORT, clientId=CLIENT_ID)
                    logger.info("Connected to IB Gateway")
                    
                    # Start data stream
                    bars = ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr='1800 S',
                        barSizeSetting='1 min',
                        whatToShow='MIDPOINT',
                        useRTH=True,
                        keepUpToDate=True
                    )
                    bars.updateEvent += on_bar_update
                    logger.info("Data stream started")
                
                ib.sleep(60)
                
            else:
                if ib.isConnected():
                    logger.info("Outside trading hours - Disconnecting...")
                    ib.disconnect()
                    bars = None
                
                logger.info("Sleeping (market closed)...")
                time.sleep(300)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            if ib.isConnected():
                ib.disconnect()
            break
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            if ib.isConnected():
                ib.disconnect()
            time.sleep(60)


if __name__ == "__main__":
    main()
