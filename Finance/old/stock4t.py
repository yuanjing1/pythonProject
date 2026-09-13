from futu import *

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111, is_encrypt=False)

simple_filter = SimpleFilter()
simple_filter.filter_min = 1
simple_filter.filter_max = 10000000
simple_filter.stock_field = StockField.CUR_PRICE
simple_filter.is_no_filter = False

simple_filter_market_cap = SimpleFilter()
simple_filter_market_cap.filter_min = 0
simple_filter_market_cap.filter_max = 5000000000000
simple_filter_market_cap.stock_field = StockField.MARKET_VAL
simple_filter_market_cap.is_no_filter = False

financial_filter_gross = FinancialFilter()
financial_filter_gross.filter_min = 50
financial_filter_gross.filter_max = 100
financial_filter_gross.stock_field = StockField.GROSS_PROFIT_RATE
financial_filter_gross.is_no_filter = False
financial_filter_gross.quarter = FinancialQuarter.ANNUAL

simple_filter_pe = SimpleFilter()
simple_filter_pe.filter_min = 0
simple_filter_pe.filter_max = 40
simple_filter_pe.stock_field = StockField.PE_ANNUAL
simple_filter_pe.is_no_filter = False

financial_filter_current = FinancialFilter()
financial_filter_current.filter_min = 200
financial_filter_current.filter_max = 5000
financial_filter_current.stock_field = StockField.CURRENT_RATIO
financial_filter_current.is_no_filter = False
financial_filter_current.sort = SortDir.ASCEND
financial_filter_current.quarter = FinancialQuarter.ANNUAL

financial_filter_asset_growth = FinancialFilter()
financial_filter_asset_growth.filter_min = 20
financial_filter_asset_growth.filter_max = 100
financial_filter_asset_growth.stock_field = StockField.TOTAL_ASSETS_GROWTH_RATE
financial_filter_asset_growth.is_no_filter = False
financial_filter_asset_growth.quarter = FinancialQuarter.ANNUAL

financial_filter_net_profit = FinancialFilter()
financial_filter_net_profit.filter_min = 1000000000
financial_filter_net_profit.stock_field = StockField.NET_PROFIT
financial_filter_net_profit.is_no_filter = False
financial_filter_net_profit.quarter = FinancialQuarter.ANNUAL

ret, ls = quote_ctx.get_stock_filter(market=Market.US, filter_list=[financial_filter_net_profit, financial_filter_asset_growth, simple_filter, simple_filter_pe, simple_filter_market_cap, financial_filter_current, financial_filter_gross])
if ret == RET_OK:
    last_page, all_count, ret_list = ls
    for item in ret_list:
        print(item.stock_code)
        print(item.stock_name)
        print('Price: ', item.cur_price)
        print('current ratio: ', item[financial_filter_current])
        print('gross profit: ', item[financial_filter_gross])
        print('market cap: ', item[simple_filter_market_cap])
        print('P/E: ', item[simple_filter_pe])
    print(len(ret_list), all_count)
else:
    print('error: ', ls)
quote_ctx.close()