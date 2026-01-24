#!/usr/bin/env python3
"""
EURUSD Momentum Trading Bot - Part 2
=====================================
Course: [Your Course Name]
Authors: Tayebeh Oveisi Fardoye, Sara Eghlidi, Alejandro Arzola de Leon, Hadi Shahparvari

This script implements the Momentum trading strategy for live trading.
Deploy on server with systemd service.

Requirements:
- Python 3.8+
- ib_insync library (pip install ib_insync)
- IB Gateway running on port 4002
"""

from ib_insync import IB, Forex, MarketOrder, util
import datetime
import time
import logging

# === CONFIGURATION ===
SYMBOL = 'EURUSD'
POSITION_SIZE = 20000          # Units to trade
MOMENTUM_PERIOD = 10           # Same as backtested strategy
IB_HOST = '127.0.0.1'
IB_PORT = 4002                 # IB Gateway port (use 7497 for TWS)
CLIENT_ID = 1

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === GLOBAL VARIABLES ===
ib = IB()
contract = Forex(SYMBOL)


def is_trading_hours():
    """
    Check if within forex trading hours.
    Forex Market: Sunday 17:00 ET - Friday 17:00 ET
    """
    now = datetime.datetime.now()
    weekday = now.weekday()  # Monday=0, Sunday=6
    hour = now.hour
    
    # Saturday: Market closed all day
    if weekday == 5:
        logger.info("Saturday - Market CLOSED")
        return False
    
    # Sunday: Market opens at 17:00 (5 PM)
    if weekday == 6 and hour < 17:
        logger.info("Sunday before 17:00 - Market CLOSED")
        return False
    
    # Friday: Market closes at 17:00 (5 PM)
    if weekday == 4 and hour >= 17:
        logger.info("Friday after 17:00 - Market CLOSED")
        return False
    
    return True


def get_current_position():
    """Get current position for EUR"""
    positions = ib.positions()
    for p in positions:
        if p.contract.symbol == 'EUR':
            return p.position
    return 0


def on_bar_update(bars, hasNewBar):
    """
    Callback function for real-time bar updates.
    Implements Momentum Strategy: Buy if price > price 10 bars ago, else Sell
    """
    if not hasNewBar:
        return
    
    if len(bars) < MOMENTUM_PERIOD + 1:
        logger.warning(f"Not enough bars: {len(bars)}")
        return
    
    try:
        # Calculate Momentum Signal
        current_price = bars[-1].close
        past_price = bars[-(MOMENTUM_PERIOD + 1)].close
        momentum = current_price - past_price
        
        # Get current position
        current_pos = get_current_position()
        
        logger.info(f"Price: {current_price:.5f} | Momentum: {momentum:.5f} | Position: {current_pos}")
        
        # Trading Logic (same as backtested)
        if momentum > 0 and current_pos <= 0:
            # Momentum UP: Go LONG
            order = MarketOrder('BUY', POSITION_SIZE)
            ib.placeOrder(contract, order)
            logger.info("BUY Signal: Momentum UP")
            
        elif momentum < 0 and current_pos >= 0:
            # Momentum DOWN: Go SHORT
            order = MarketOrder('SELL', POSITION_SIZE)
            ib.placeOrder(contract, order)
            logger.info("SELL Signal: Momentum DOWN")
            
    except Exception as e:
        logger.error(f"Error in on_bar_update: {e}")


def connect_to_ib():
    """Connect to IB Gateway"""
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=CLIENT_ID)
        logger.info(f"Connected to IB Gateway ({IB_HOST}:{IB_PORT})")
        return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False


def disconnect_from_ib():
    """Disconnect from IB Gateway"""
    if ib.isConnected():
        ib.disconnect()
        logger.info("Disconnected from IB Gateway")


def start_data_stream():
    """Start real-time data streaming"""
    try:
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
        logger.info("Real-time data stream started")
        return bars
    except Exception as e:
        logger.error(f"Error starting data stream: {e}")
        return None


def main():
    """Main trading loop with trading hours check"""
    logger.info("=" * 50)
    logger.info("EURUSD MOMENTUM TRADING BOT STARTED")
    logger.info("=" * 50)
    
    bars = None
    
    while True:
        try:
            if is_trading_hours():
                # === INSIDE TRADING HOURS ===
                if not ib.isConnected():
                    logger.info("Trading hours - Connecting...")
                    if connect_to_ib():
                        bars = start_data_stream()
                    else:
                        logger.warning("Connection failed, retrying in 60s...")
                        time.sleep(60)
                        continue
                
                # Keep processing events
                ib.sleep(60)
                
            else:
                # === OUTSIDE TRADING HOURS ===
                if ib.isConnected():
                    logger.info("Outside trading hours - Disconnecting...")
                    disconnect_from_ib()
                    bars = None
                
                # Sleep longer when market is closed
                logger.info("Sleeping for 5 minutes (market closed)...")
                time.sleep(300)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
            disconnect_from_ib()
            break
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            disconnect_from_ib()
            time.sleep(60)


if __name__ == "__main__":
    main()
