from datetime import datetime,timedelta
from src.super.ESModel import ESModel


class EStock(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        
    }
    MAPPING                             = {
        "settings"                      : {
            "index"                     : {
                "refresh_interval"      : "1s",
            }
        },
        "mappings"                      : {
            "dynamic"                   : "false", 
            "properties"                : {
                "symbol"                : {"type": "keyword"}, 
                "name"                  : {"type": "text"},
                "price"                 : {"type": "float"},
                "price_change"          : {"type": "float"},
                "price_change_pct"      : {"type": "float"},
                "buy"                   : {"type": "float"},
                "sell"                  : {"type": "float"},
                "previous_close"        : {"type": "float"},
                "open"                  : {"type": "float"},
                "high"                  : {"type": "float"},
                "low"                   : {"type": "float"},
                "volume"                : {"type": "float"},
                "turnover"              : {"type": "float"},
        
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"} 
            }
        }
    }

class EStockGdp(ESModel):
    PRIVACY_ATTRIBUTES                  = ['_score']
    DEFAULT_ATTRVALUES                  = {
        
    }
    MAPPING                             = {
        "settings"                      : {
            "index"                     : {
                "refresh_interval"      : "1s",
            }
        },
        "mappings"                      : {
            "dynamic"                   : "false", 
            "properties"                : {
                "text"                  : {"type": "text"},
                "updated"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"}, 
                "created"               : {"type": "date","format": "yyyy-MM-dd HH:mm:ss"} 
            }
        }
    }