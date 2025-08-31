# Binance Stream
## Spot

- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#exchange-information

### BinanceSpotExchangeInfoSymbol
---

**Information:**

- info 
  ```
  https://api.binance.com/api/v3/exchangeInfo
  ```


**Ref:** 
- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#exchange-information
**Response:**
```
{
  "timezone": "UTC",
  "serverTime": 1565246363776,
  "rateLimits": [
    {
      // These are defined in the `ENUM definitions` section under `Rate Limiters (rateLimitType)`.
      // All limits are optional
    }
  ],
  "exchangeFilters": [
    // These are the defined filters in the `Filters` section.
    // All filters are optional.
  ],
  "symbols": [
    {
      "symbol": "ETHBTC",
      "status": "TRADING",
      "baseAsset": "ETH",
      "baseAssetPrecision": 8,
      "quoteAsset": "BTC",
      "quotePrecision": 8, // will be removed in future api versions (v4+)
      "quoteAssetPrecision": 8,
      "baseCommissionPrecision": 8,
      "quoteCommissionPrecision": 8,
      "orderTypes": [
        "LIMIT",
        "LIMIT_MAKER",
        "MARKET",
        "STOP_LOSS",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT",
        "TAKE_PROFIT_LIMIT"
      ],
      "icebergAllowed": true,
      "ocoAllowed": true,
      "otoAllowed": true,
      "quoteOrderQtyMarketAllowed": true,
      "allowTrailingStop": false,
      "cancelReplaceAllowed":false,
      "amendAllowed":false,
      "pegInstructionsAllowed": true,
      "isSpotTradingAllowed": true,
      "isMarginTradingAllowed": true,
      "filters": [
        // These are defined in the Filters section.
        // All filters are optional
      ],
      "permissions": [],
      "permissionSets": [
        [
          "SPOT",
          "MARGIN"
        ]
      ],
      "defaultSelfTradePreventionMode": "NONE",
      "allowedSelfTradePreventionModes": [
        "NONE"
      ]
    }
  ],
  // Optional field. Present only when SOR is available.
  // https://github.com/binance/binance-spot-api-docs/blob/master/faqs/sor_faq.md
  "sors": [
    {
      "baseAsset": "BTC",
      "symbols": [
        "BTCUSDT",
        "BTCUSDC"
      ]
    }
  ]
}
```
**Schema**
```
{
      "symbol": "ETHBTC",
      "status": "TRADING",
      "baseAsset": "ETH",
      "baseAssetPrecision": 8,
      "quoteAsset": "BTC",
      "quotePrecision": 8, // will be removed in future api versions (v4+)
      "quoteAssetPrecision": 8,
      "baseCommissionPrecision": 8,
      "quoteCommissionPrecision": 8,
      "orderTypes": [
        "LIMIT",
        "LIMIT_MAKER",
        "MARKET",
        "STOP_LOSS",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT",
        "TAKE_PROFIT_LIMIT"
      ],
      "icebergAllowed": true,
      "ocoAllowed": true,
      "otoAllowed": true,
      "quoteOrderQtyMarketAllowed": true,
      "allowTrailingStop": false,
      "cancelReplaceAllowed":false,
      "amendAllowed":false,
      "pegInstructionsAllowed": true,
      "isSpotTradingAllowed": true,
      "isMarginTradingAllowed": true,
      "filters": [
        // These are defined in the Filters section.
        // All filters are optional
      ],
      "permissions": [],
      "permissionSets": [
        [
          "SPOT",
          "MARGIN"
        ]
      ],
      "defaultSelfTradePreventionMode": "NONE",
      "allowedSelfTradePreventionModes": [
        "NONE"
      ]
    }
```

### BinanceSpotKlineDaily
---

**Information:**

- info 
  ```
  https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=$START&endTime=$END
  ```


**Ref:** 
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data

**Response:**
```
[
  [
    1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
  ]
]
```
**Schema**
{
	1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
}
```

## Future USDT

- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#exchange-information

### BinanceFutureUSDTExchangeInfoSymbol
---

**Information:**

- info 
  ```
  https://fapi.binance.com/fapi/v1/exchangeInfo
  ```


**Ref:** 
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information

**Response:**
```
{
	"exchangeFilters": [],
 	"rateLimits": [
 		{
 			"interval": "MINUTE",
   			"intervalNum": 1,
   			"limit": 2400,
   			"rateLimitType": "REQUEST_WEIGHT" 
   		},
  		{
  			"interval": "MINUTE",
   			"intervalNum": 1,
   			"limit": 1200,
   			"rateLimitType": "ORDERS"
   		}
   	],
 	"serverTime": 1565613908500,    // Ignore please. If you want to check current server time, please check via "GET /fapi/v1/time"
 	"assets": [ // assets information
 		{
 			"asset": "BTC",
   			"marginAvailable": true, // whether the asset can be used as margin in Multi-Assets mode
   			"autoAssetExchange": "-0.10" // auto-exchange threshold in Multi-Assets margin mode
   		},
 		{
 			"asset": "USDT",
   			"marginAvailable": true,
   			"autoAssetExchange": "0"
   		},
 		{
 			"asset": "BNB",
   			"marginAvailable": false,
   			"autoAssetExchange": null
   		}
   	],
 	"symbols": [
 		{
 			"symbol": "BLZUSDT",
 			"pair": "BLZUSDT",
 			"contractType": "PERPETUAL",
 			"deliveryDate": 4133404800000,
 			"onboardDate": 1598252400000,
 			"status": "TRADING",
 			"maintMarginPercent": "2.5000",   // ignore
 			"requiredMarginPercent": "5.0000",  // ignore
 			"baseAsset": "BLZ", 
 			"quoteAsset": "USDT",
 			"marginAsset": "USDT",
 			"pricePrecision": 5,	// please do not use it as tickSize
 			"quantityPrecision": 0, // please do not use it as stepSize
 			"baseAssetPrecision": 8,
 			"quotePrecision": 8, 
 			"underlyingType": "COIN",
 			"underlyingSubType": ["STORAGE"],
 			"settlePlan": 0,
 			"triggerProtect": "0.15", // threshold for algo order with "priceProtect"
 			"filters": [
 				{
 					"filterType": "PRICE_FILTER",
     				"maxPrice": "300",
     				"minPrice": "0.0001", 
     				"tickSize": "0.0001"
     			},
    			{
    				"filterType": "LOT_SIZE", 
     				"maxQty": "10000000",
     				"minQty": "1",
     				"stepSize": "1"
     			},
    			{
    				"filterType": "MARKET_LOT_SIZE",
     				"maxQty": "590119",
     				"minQty": "1",
     				"stepSize": "1"
     			},
     			{
    				"filterType": "MAX_NUM_ORDERS",
    				"limit": 200
  				},
  				{
    				"filterType": "MAX_NUM_ALGO_ORDERS",
    				"limit": 10
  				},
  				{
  					"filterType": "MIN_NOTIONAL",
  					"notional": "5.0", 
  				},
  				{
    				"filterType": "PERCENT_PRICE",
    				"multiplierUp": "1.1500",
    				"multiplierDown": "0.8500",
    				"multiplierDecimal": "4"
    			}
   			],
 			"OrderType": [
   				"LIMIT",
   				"MARKET",
   				"STOP",
   				"STOP_MARKET",
   				"TAKE_PROFIT",
   				"TAKE_PROFIT_MARKET",
   				"TRAILING_STOP_MARKET" 
   			],
   			"timeInForce": [
   				"GTC", 
   				"IOC", 
   				"FOK", 
   				"GTX" 
 			],
 			"liquidationFee": "0.010000",	// liquidation fee rate
   			"marketTakeBound": "0.30",	// the max price difference rate( from mark price) a market order can make
 		}
   	],
	"timezone": "UTC" 
}
```

**Schema**
```
{
 			"symbol": "BLZUSDT",
 			"pair": "BLZUSDT",
 			"contractType": "PERPETUAL",
 			"deliveryDate": 4133404800000,
 			"onboardDate": 1598252400000,
 			"status": "TRADING",
 			"maintMarginPercent": "2.5000",   // ignore
 			"requiredMarginPercent": "5.0000",  // ignore
 			"baseAsset": "BLZ", 
 			"quoteAsset": "USDT",
 			"marginAsset": "USDT",
 			"pricePrecision": 5,	// please do not use it as tickSize
 			"quantityPrecision": 0, // please do not use it as stepSize
 			"baseAssetPrecision": 8,
 			"quotePrecision": 8, 
 			"underlyingType": "COIN",
 			"underlyingSubType": ["STORAGE"],
 			"settlePlan": 0,
 			"triggerProtect": "0.15", // threshold for algo order with "priceProtect"
 			"filters": [
 				{
 					"filterType": "PRICE_FILTER",
     				"maxPrice": "300",
     				"minPrice": "0.0001", 
     				"tickSize": "0.0001"
     			},
    			{
    				"filterType": "LOT_SIZE", 
     				"maxQty": "10000000",
     				"minQty": "1",
     				"stepSize": "1"
     			},
    			{
    				"filterType": "MARKET_LOT_SIZE",
     				"maxQty": "590119",
     				"minQty": "1",
     				"stepSize": "1"
     			},
     			{
    				"filterType": "MAX_NUM_ORDERS",
    				"limit": 200
  				},
  				{
    				"filterType": "MAX_NUM_ALGO_ORDERS",
    				"limit": 10
  				},
  				{
  					"filterType": "MIN_NOTIONAL",
  					"notional": "5.0", 
  				},
  				{
    				"filterType": "PERCENT_PRICE",
    				"multiplierUp": "1.1500",
    				"multiplierDown": "0.8500",
    				"multiplierDecimal": "4"
    			}
   			],
 			"OrderType": [
   				"LIMIT",
   				"MARKET",
   				"STOP",
   				"STOP_MARKET",
   				"TAKE_PROFIT",
   				"TAKE_PROFIT_MARKET",
   				"TRAILING_STOP_MARKET" 
   			],
   			"timeInForce": [
   				"GTC", 
   				"IOC", 
   				"FOK", 
   				"GTX" 
 			],
 			"liquidationFee": "0.010000",	// liquidation fee rate
   			"marketTakeBound": "0.30",	// the max price difference rate( from mark price) a market order can make
 		}
```

## Future COINM

- https://developers.binance.com/docs/binance-spot-api-docs/rest-api/general-endpoints#exchange-information

### BinanceFutureUSDTExchangeInfoSymbol
---

**Information:**

- info 
  ```
  https://fapi.binance.com/fapi/v1/exchangeInfo
  ```


**Ref:** 
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information

**Response:**

```
{
	"exchangeFilters": [],
 	"rateLimits": [ 
 		{
 			"interval": "MINUTE", 
   			"intervalNum": 1, 
   			"limit": 6000, 
   			"rateLimitType": "REQUEST_WEIGHT" 
   		},
  		{
  			"interval": "MINUTE",
   			"intervalNum": 1,
   			"limit": 6000,
   			"rateLimitType": "ORDERS"
   		}
   	],
 	"serverTime": 1565613908500, // Ignore please. If you want to check current server time, please check via "GET /dapi/v1/time"
 	"symbols": [ // contract symbols
 		{
 			"filters": [
 				{
 					"filterType": "PRICE_FILTER", 
     				"maxPrice": "100000", 
     				"minPrice": "0.1", 
     				"tickSize": "0.1" 
     			},
    			{
    				"filterType": "LOT_SIZE", 
     				"maxQty": "100000", 
     				"minQty": "1", 
     				"stepSize": "1" 
     			},
    			{
    				"filterType": "MARKET_LOT_SIZE", 
     				"maxQty": "100000", 
     				"minQty": "1", 
     				"stepSize": "1" 
     			},
     			{
    				"filterType": "MAX_NUM_ORDERS", 
    				"limit": 200
  				},
  				{
    				"filterType": "PERCENT_PRICE", 
    				"multiplierUp": "1.0500", 
    				"multiplierDown": "0.9500", 
    				"multiplierDecimal": "4"
  				}
    		],
   			"OrderType": [ 
   				"LIMIT", 
   				"MARKET", 
   				"STOP",
   				"TAKE_PROFIT",
   				"TRAILING_STOP_MARKET"
   			],
   			"timeInForce": [
   				"GTC",
   				"IOC",
   				"FOK",
   				"GTX"
   			],
   			"liquidationFee": "0.010000",	// liquidation fee rate
   			"marketTakeBound": "0.30",	// the max price difference rate( from mark price) a market order can make
   			"symbol": "BTCUSD_200925", // contract symbol name
   			"pair": "BTCUSD",  // underlying symbol
   			"contractType": "CURRENT_QUARTER", 
   			"deliveryDate": 1601020800000,
   			"onboardDate": 1590739200000,
   			"contractStatus": "TRADING", 
   			"contractSize": 100,    
   			"quoteAsset": "USD",
   			"baseAsset": "BTC",   
   			"marginAsset": "BTC",
   			"pricePrecision": 1,	// please do not use it as tickSize
		   	"quantityPrecision": 0,	// please do not use it as stepSize
		   	"baseAssetPrecision": 8,
		   	"quotePrecision": 8,
		   	"equalQtyPrecision": 4,	 // ignore
		   	"triggerProtect": "0.0500",	// threshold for algo order with "priceProtect"
		   	"maintMarginPercent": "2.5000",  // ignore
		   	"requiredMarginPercent": "5.0000",  // ignore
		   	"underlyingType": "COIN", 
		   	"underlyingSubType": []	
   		}
   	],
	"timezone": "UTC"
}
```

**Schema**
```
{
 			"filters": [
 				{
 					"filterType": "PRICE_FILTER", 
     				"maxPrice": "100000", 
     				"minPrice": "0.1", 
     				"tickSize": "0.1" 
     			},
    			{
    				"filterType": "LOT_SIZE", 
     				"maxQty": "100000", 
     				"minQty": "1", 
     				"stepSize": "1" 
     			},
    			{
    				"filterType": "MARKET_LOT_SIZE", 
     				"maxQty": "100000", 
     				"minQty": "1", 
     				"stepSize": "1" 
     			},
     			{
    				"filterType": "MAX_NUM_ORDERS", 
    				"limit": 200
  				},
  				{
    				"filterType": "PERCENT_PRICE", 
    				"multiplierUp": "1.0500", 
    				"multiplierDown": "0.9500", 
    				"multiplierDecimal": "4"
  				}
    		],
   			"OrderType": [ 
   				"LIMIT", 
   				"MARKET", 
   				"STOP",
   				"TAKE_PROFIT",
   				"TRAILING_STOP_MARKET"
   			],
   			"timeInForce": [
   				"GTC",
   				"IOC",
   				"FOK",
   				"GTX"
   			],
   			"liquidationFee": "0.010000",	// liquidation fee rate
   			"marketTakeBound": "0.30",	// the max price difference rate( from mark price) a market order can make
   			"symbol": "BTCUSD_200925", // contract symbol name
   			"pair": "BTCUSD",  // underlying symbol
   			"contractType": "CURRENT_QUARTER", 
   			"deliveryDate": 1601020800000,
   			"onboardDate": 1590739200000,
   			"contractStatus": "TRADING", 
   			"contractSize": 100,    
   			"quoteAsset": "USD",
   			"baseAsset": "BTC",   
   			"marginAsset": "BTC",
   			"pricePrecision": 1,	// please do not use it as tickSize
		   	"quantityPrecision": 0,	// please do not use it as stepSize
		   	"baseAssetPrecision": 8,
		   	"quotePrecision": 8,
		   	"equalQtyPrecision": 4,	 // ignore
		   	"triggerProtect": "0.0500",	// threshold for algo order with "priceProtect"
		   	"maintMarginPercent": "2.5000",  // ignore
		   	"requiredMarginPercent": "5.0000",  // ignore
		   	"underlyingType": "COIN", 
		   	"underlyingSubType": []	
   		}
```

### BinanceFutureCOINMKlineDaily
---

**Information:**

- info 
  ```
  https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=$START&endTime=$END
  ```


**Ref:** 
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data

**Response:**
```
[
  [
    1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
  ]
]
```

**Schema**
{
	1499040000000,      // Open time
	"0.01634790",       // Open
	"0.80000000",       // High
	"0.01575800",       // Low
	"0.01577100",       // Close
	"148976.11427815",  // Volume
	1499644799999,      // Close time
	"2434.19055334",    // Quote asset volume
	308,                // Number of trades
	"1756.87402397",    // Taker buy base asset volume
	"28.46694368",      // Taker buy quote asset volume
	"17928899.62484339" // Ignore.
}
```