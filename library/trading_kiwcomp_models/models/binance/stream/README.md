# Binance Stream
## Future COINM
- WebSocket API General Info
 : https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-api-general-info

### BinanceStreamFuturesCOINMKline
---

**Information:**

- The Kline/Candlestick Stream push updates to the current klines/candlestick every 250 milliseconds (if existing).

**Ref:** 
- https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-market-streams/Kline-Candlestick-Streams

**Schema:**
```
{
  "e":"kline",				// Event type
  "E":1591261542539,		// Event time
  "s":"BTCUSD_200626",		// Symbol
  "k":{
    "t":1591261500000,		// Kline start time
    "T":1591261559999,		// Kline close time
    "s":"BTCUSD_200626",	// Symbol
    "i":"1m",				// Interval
    "f":606400,				// First trade ID
    "L":606430,				// Last trade ID
    "o":"9638.9",			// Open price
    "c":"9639.8",			// Close price
    "h":"9639.8",			// High price
    "l":"9638.6",			// Low price
    "v":"156",				// volume
    "n":31,					// Number of trades
    "x":false,				// Is this kline closed?
    "q":"1.61836886",		// Base asset volume
    "V":"73",				// Taker buy volume
    "Q":"0.75731156",		// Taker buy base asset volume
    "B":"0"					// Ignore
  }
}
```

### BinanceStreamFuturesCOINMMarkPriceUpdate

**Information:**

- Mark price update stream

**Ref:** 
- https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-market-streams/Mark-Price-Stream

**Schema:**
```
{
	"e":"markPriceUpdate",	// Event type
  	"E":1596095725000,		// Event time
   	"s":"BTCUSD_201225",	// Symbol
  	"p":"10934.62615417",	// Mark Price
  	"P":"10962.17178236",	// Estimated Settle Price, only useful in the last hour before the settlement starts.
	"i":"10933.62615417",   // Index Price 
  	"r":"",					// funding rate for perpetual symbol, "" will be shown for delivery symbol
  	"T":0					// next funding time for perpetual symbol, 0 will be shown for delivery symbol
}
```

## Future USDT
- WebSocket API General Info
 : https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-api-general-info

### BinanceStreamFuturesUSDTKline
---

**Information:**

- The Kline/Candlestick Stream push updates to the current klines/candlestick every 250 milliseconds (if existing).


**Ref:** 
- https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Kline-Candlestick-Streams

**Schema:**
```
{
  "e": "kline",     // Event type
  "E": 1638747660000,   // Event time
  "s": "BTCUSDT",    // Symbol
  "k": {
    "t": 1638747660000, // Kline start time
    "T": 1638747719999, // Kline close time
    "s": "BTCUSDT",  // Symbol
    "i": "1m",      // Interval
    "f": 100,       // First trade ID
    "L": 200,       // Last trade ID
    "o": "0.0010",  // Open price
    "c": "0.0020",  // Close price
    "h": "0.0025",  // High price
    "l": "0.0015",  // Low price
    "v": "1000",    // Base asset volume
    "n": 100,       // Number of trades
    "x": false,     // Is this kline closed?
    "q": "1.0000",  // Quote asset volume
    "V": "500",     // Taker buy base asset volume
    "Q": "0.500",   // Taker buy quote asset volume
    "B": "123456"   // Ignore
  }
}
```

### BinanceStreamFuturesUSDTMarkPriceUpdate
---

**Information:**

- Mark price and funding rate for a single symbol pushed every 3 seconds or every second.


**Ref:** 
- https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Mark-Price-Stream

**Schema:**

```
{
"e": "markPriceUpdate",  	// Event type
"E": 1562305380000,      	// Event time
"s": "BTCUSDT",          	// Symbol
"p": "11794.15000000",   	// Mark price
"i": "11784.62659091",		// Index price
"P": "11784.25641265",		// Estimated Settle Price, only useful in the last hour before the settlement starts
"r": "0.00038167",       	// Funding rate
"T": 1562306400000       	// Next funding time
}
```

## Spot
https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams

### BinanceStreamSpotKline
---
**Information:**

- The Kline/Candlestick Stream push updates to the current klines/candlestick every second in UTC+0 timezone




**Ref:** 
- https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#klinecandlestick-streams-for-utc

**Schema:**

```
{
  "e": "kline",         // Event type
  "E": 1672515782136,   // Event time
  "s": "BNBBTC",        // Symbol
  "k": {
    "t": 1672515780000, // Kline start time
    "T": 1672515839999, // Kline close time
    "s": "BNBBTC",      // Symbol
    "i": "1m",          // Interval
    "f": 100,           // First trade ID
    "L": 200,           // Last trade ID
    "o": "0.0010",      // Open price
    "c": "0.0020",      // Close price
    "h": "0.0025",      // High price
    "l": "0.0015",      // Low price
    "v": "1000",        // Base asset volume
    "n": 100,           // Number of trades
    "x": false,         // Is this kline closed?
    "q": "1.0000",      // Quote asset volume
    "V": "500",         // Taker buy base asset volume
    "Q": "0.500",       // Taker buy quote asset volume
    "B": "123456"       // Ignore
  }
}
```