import os
import re
import time
import json
import requests
import threading
import traceback
from json_manage import *
from binance_key import *
from config import *
from datetime import datetime, timedelta
import dateutil.parser as dparser



ARTICLES_URL = 'https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=48&pageNo=1&pageSize=30'
ARTICLE      = 'https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode='
existing_assets = ["BTC","LTC","ETH","NEO","BNB","QTUM","EOS","SNT","BNT","GAS","BCC","USDT","HSR","OAX","DNT","MCO","ICN","ZRX","OMG","WTC","YOYO","LRC","TRX","SNGLS","STRAT","BQX","FUN","KNC","CDT","XVG","IOTA","SNM","LINK","CVC","TNT","REP","MDA","MTL","SALT","NULS","SUB","STX","MTH","ADX","ETC","ENG","ZEC","AST","GNT","DGD","BAT","DASH","POWR","BTG","REQ","XMR","EVX","VIB","ENJ","VEN","ARK","XRP","MOD","STORJ","KMD","RCN","EDO","DATA","DLT","MANA","PPT","RDN","GXS","AMB","ARN","BCPT","CND","GVT","POE","BTS","FUEL","XZC","QSP","LSK","BCD","TNB","ADA","LEND","XLM","CMT","WAVES","WABI","GTO","ICX","OST","ELF","AION","WINGS","BRD","NEBL","NAV","VIBE","LUN","TRIG","APPC","CHAT","RLC","INS","PIVX","IOST","STEEM","NANO","AE","VIA","BLZ","SYS","RPX","NCASH","POA","ONT","ZIL","STORM","XEM","WAN","WPR","QLC","GRS","CLOAK","LOOM","BCN","TUSD","ZEN","SKY","THETA","IOTX","QKC","AGI","NXS","SC","NPXS","KEY","NAS","MFT","DENT","IQ","ARDR","HOT","VET","DOCK","POLY","VTHO","ONG","PHX","HC","GO","PAX","RVN","DCR","USDC","MITH","BCHABC","BCHSV","REN","BTT","USDS","FET","TFUEL","CELR","MATIC","ATOM","PHB","ONE","FTM","BTCB","USDSB","CHZ","COS","ALGO","ERD","DOGE","BGBP","DUSK","ANKR","WIN","TUSDB","COCOS","PERL","TOMO","BUSD","BAND","BEAM","HBAR","XTZ","NGN","DGB","NKN","GBP","EUR","KAVA","RUB","UAH","ARPA","TRY","CTXC","AERGO","BCH","TROY","BRL","VITE","FTT","AUD","OGN","DREP","BULL","BEAR","ETHBULL","ETHBEAR","XRPBULL","XRPBEAR","EOSBULL","EOSBEAR","TCT","WRX","LTO","ZAR","MBL","COTI","BKRW","BNBBULL","BNBBEAR","HIVE","STPT","SOL","IDRT","CTSI","CHR","BTCUP","BTCDOWN","HNT","JST","FIO","BIDR","STMX","MDT","PNT","COMP","IRIS","MKR","SXP","SNX","DAI","ETHUP","ETHDOWN","ADAUP","ADADOWN","LINKUP","LINKDOWN","DOT","RUNE","BNBUP","BNBDOWN","XTZUP","XTZDOWN","AVA","BAL","YFI","SRM","ANT","CRV","SAND","OCEAN","NMR","LUNA","IDEX","RSR","PAXG","WNXM","TRB","EGLD","BZRX","WBTC","KSM","SUSHI","YFII","DIA","BEL","UMA","EOSUP","TRXUP","EOSDOWN","TRXDOWN","XRPUP","XRPDOWN","DOTUP","DOTDOWN","NBS","WING","SWRV","LTCUP","LTCDOWN","CREAM","UNI","OXT","SUN","AVAX","BURGER","BAKE","FLM","SCRT","XVS","CAKE","SPARTA","UNIUP","UNIDOWN","ALPHA","ORN","UTK","NEAR","VIDT","AAVE","FIL","SXPUP","SXPDOWN","INJ","FILDOWN","FILUP","YFIUP","YFIDOWN","CTK","EASY","AUDIO","BCHUP","BCHDOWN","BOT","AXS","AKRO","HARD","KP3R","RENBTC","SLP","STRAX","UNFI","CVP","BCHA","FOR","FRONT","ROSE","HEGIC","AAVEUP","AAVEDOWN","PROM","BETH","SKL","GLM","SUSD","COVER","GHST","SUSHIUP","SUSHIDOWN","XLMUP","XLMDOWN","DF","JUV","PSG","BVND","GRT","CELO","TWT","REEF","OG","ATM","ASR","1INCH","RIF","BTCST","TRU","DEXE","CKB","FIRO","LIT","PROS","VAI","SFP","FXS","DODO","AUCTION","UFT","ACM","PHA","TVK","BADGER","FIS","OM","POND","ALICE","DEGO","BIFI","LINA"]

key_words = ['Futures', 'Isolated', 'Margin', 'Launchpool', 'Launchpad', 'Cross', 'Perpetual']
filter_List = ['body', 'type', 'catalogId', 'catalogName', 'publishDate']

file = 'announcements.json'
schedules_file = 'scheduled_order.json'
executed_trades_file = 'executed_trades.json'
executed_sells_file = 'executed_sells_trades.json'

executed_queque = []
pair_Dict = {}

cnf = load_config('config.yml')
client = load_binance_creds(r'auth.yml')

telegram_status = True

telegram_keys=[]

if os.path.exists('telegram.yml'):
    telegram_keys = load_config('telegram.yml')

else: telegram_status = False


def telegram_bot_sendtext(bot_message):

    send_text = 'https://api.telegram.org/bot' + str(telegram_keys['telegram_key']) + '/sendMessage?chat_id=' + str(telegram_keys['chat_id']) + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()['result']['message_id']

def telegram_delete_message(message_id):

    send_text = 'https://api.telegram.org/bot' + str(telegram_keys['telegram_key']) + '/deleteMessage?chat_id=' + str(telegram_keys['chat_id']) + '&message_id=' + str(message_id)

    requests.get(send_text)


class Send_Without_Spamming():
    
    def __init__(self):
        self.id =0000
        self.first = True
    
    def send(self, message):
        if telegram_status:
            if self.first:
                self.first = False
                self.id = telegram_bot_sendtext(message)
            else:
                telegram_delete_message(self.id)
                self.id = telegram_bot_sendtext(message)
        else:
            print(message)
        
    def kill(self, pair):
        if telegram_status:
            telegram_delete_message(self.id)
            del pair_Dict[pair] 


def killSpam(pair):
    try:
        pair_Dict[pair].kill(pair)
    except Exception:
        pass
        


def sendSpam(pair, message):
    try:
        pair_Dict[pair].send(message)
    except Exception:
        pair_Dict[pair] = Send_Without_Spamming()
        pair_Dict[pair].send(message)





tp = cnf['TRADE_OPTIONS']['TP']
sl = cnf['TRADE_OPTIONS']['SL']

tsl_mode = cnf['TRADE_OPTIONS']['ENABLE_TSL']
tsl = cnf['TRADE_OPTIONS']['TSL']
ttp = cnf['TRADE_OPTIONS']['TTP']

pairing = cnf['TRADE_OPTIONS']['PAIRING']
ammount = cnf['TRADE_OPTIONS']['QUANTITY']
frequency = cnf['TRADE_OPTIONS']['RUN_EVERY']

test_mode = cnf['TRADE_OPTIONS']['TEST']
delay_mode = cnf['TRADE_OPTIONS']['CONSIDER_DELAY']
percentage = cnf['TRADE_OPTIONS']['PERCENTAGE']

existing_assets.remove(pairing)
regex = '\S{2,6}?/'+ pairing

def sendmsg(message):
    print(message)
    if telegram_status:
        threading.Thread(target=telegram_bot_sendtext, args=(message,)).start()
    else:
        print(message)


def ping_binance():
    sum = 0
    for i in range(3):
        time_before = datetime.timestamp(datetime.now())
        client.ping()
        time_after = datetime.timestamp(datetime.now())
        sum += (time_after - time_before)
    return (sum / 3)

####announcements

def get_Announcements():
    unfiltered_Articles = requests.get(ARTICLES_URL).json()['data']['articles']
    articles = []

    for article in unfiltered_Articles:
        flag = True
        for word in key_words:
            if word in article['title']:
                flag = False
        if flag:
            articles.append(article)
                

    for article in articles:
        for undesired_Data in filter_List:
            if undesired_Data in article:
                del article[undesired_Data]
    
    return articles


def get_Pair_and_DateTime(ARTICLE_CODE):
    
    new_Coin = requests.get(ARTICLE+ARTICLE_CODE).json()['data']['seoDesc']
    try:
        datetime = dparser.parse(new_Coin, fuzzy=True, ignoretz=True)
    
        raw_pairs = re.findall(regex, new_Coin)
        pairs = []

        for pair in raw_pairs:
            present= False
            for j in existing_assets:
                if j in pair:
                    present = True
                    break
            if present == False:
                pairs.append(pair.replace('/', ''))
        return [datetime, pairs]
    except Exception as e:
        print(e)
        return None
    

####orders

def get_price(coin):
     return client.get_ticker(symbol=coin)['lastPrice']

def create_order(pair, usdt_to_spend, action):
    try:
        order = client.create_order(
            symbol = pair,
            side = action,
            type = 'MARKET',
            quoteOrderQty = usdt_to_spend,
            recvWindow = "10000"
        )
    except Exception as exception:       
        wrong = traceback.format_exc(limit=None, chain=True)
        sendmsg(wrong)
    return order

def executed_orders():
    global executed_queque
    while True:
        if len(executed_queque) > 0:
            if os.path.exists(executed_trades_file):
                existing_file = load_json(executed_trades_file)
                existing_file += executed_queque
            else: 
                existing_file = executed_queque
            save_json(executed_trades_file, existing_file)
            executed_queque = []
        time.sleep(0.1)
            


def schedule_Order(time_And_Pair, announcement):
    try:
        scheduled_order = {'time':time_And_Pair[0].strftime("%Y-%m-%d %H:%M:%S"), 'pairs':time_And_Pair[1]}

        sendmsg(f'Scheduled an order for: {time_And_Pair[1]} at: {time_And_Pair[0]}')
        update_json(schedules_file, scheduled_order)
        update_json(file, announcement)
    except Exception as exception:       
        wrong = traceback.format_exc(limit=None, chain=True)
        sendmsg(wrong)


def place_Order_On_Time(time_till_live, pair, threads):
    delay = 0
    global executed_queque
    try:
        if delay_mode:
            delay = (ping_binance() * percentage)
            time_till_live = (time_till_live - timedelta(seconds = delay))

        time_to_wait = ((time_till_live - datetime.utcnow()).total_seconds() - 10)
        time.sleep(time_to_wait)
        order = {}

        if test_mode:
            price = get_price(pair)
            while True:
                if (datetime.utcnow() - timedelta(seconds = 1) <= time_till_live <= datetime.utcnow() - timedelta(seconds = delay * 0.9)):
                    order = {
                        "symbol": pair,
                        "transactTime": datetime.timestamp(datetime.now()),
                        "price": price,
                        "origQty": ammount/float(price),
                        "executedQty": ammount/float(price),
                        "cummulativeQuoteQty": ammount,
                        "status": "FILLED",
                        "type": "MARKET",
                        "side": "BUY"
                        }
                    break
        else:
            while True:
                if (datetime.utcnow() - timedelta(seconds = 1) <= time_till_live <= datetime.utcnow() - timedelta(seconds = delay * 0.9)):
                    order = create_order(pair, ammount, 'BUY')
                    break
        order['tp'] = tp
        order['sl'] = sl
        amount = order['executedQty']
        price =order['price']
        if price <= 0.00001:
            price = get_price(pair)
        sendmsg(f'Bougth {amount} of {pair} at {price}')
        executed_queque.append(order)
    except Exception as exception:       
        wrong = traceback.format_exc(limit=None, chain=True)
        sendmsg(wrong)
######


def check_Schedules():
    try:
        if os.path.exists(schedules_file):
            unfiltered_schedules = load_json(schedules_file)
            schedules = []

            for schedule in unfiltered_schedules:

                flag = True
                datetime = dparser.parse(schedule['time'], fuzzy=True, ignoretz=True)

                if datetime < datetime.utcnow():
                    flag = False

                if flag:
                    schedules.append(schedule)

                    for pair in schedule['pairs']:
                        threading.Thread(target=place_Order_On_Time, args=(datetime, pair, threading.active_count() + 1)).start()
                        sendmsg(f'Found scheduled order for: {pair} adding it to new thread')
            save_json(schedules_file, schedules)
    except Exception as exception:       
        wrong = traceback.format_exc(limit=None, chain=True)
        sendmsg(wrong)
                

def sell():
    while True:
        try:
            flag_update = False
            not_sold_orders = []
            order = []
            if os.path.exists(executed_trades_file):
                order = load_json(executed_trades_file)
            if len(order) > 0:
                for coin in list(order):

                    # store some necesarry trade info for a sell
                    stored_price = float(coin['fills'][0]['price'])
                    coin_tp = coin['tp']
                    coin_sl = coin['sl']
                    volume = round(float(coin['executedQty']) - float(coin['fills'][0]['commission']),2)
                    symbol = coin['symbol']

                    last_price = get_price(symbol)

                    # update stop loss and take profit values if threshold is reached
                    if float(last_price) > stored_price + (stored_price * float(coin_tp) /100) and tsl_mode:
                        # increase as absolute value for TP
                        new_tp = float(last_price) + (float(last_price)*ttp /100)
                        # convert back into % difference from when the coin was bought
                        new_tp = float( (new_tp - stored_price) / stored_price*100)

                        # same deal as above, only applied to trailing SL
                        new_sl = float(last_price) - (float(last_price)*tsl /100)
                        new_sl = float((new_sl - stored_price) / stored_price*100)

                        # new values to be added to the json file
                        coin['tp'] = new_tp
                        coin['sl'] = new_sl
                        not_sold_orders.append(coin)
                        flag_update = True

                        threading.Thread(target=sendSpam, args=(symbol, f'Updated tp: {round(new_tp, 3)} and sl: {round(new_sl, 3)} for: {symbol}')).start()
                    # close trade if tsl is reached or trail option is not enabled
                    elif float(last_price) < stored_price - (stored_price*sl /100) or float(last_price) > stored_price + (stored_price*tp /100) and not tsl_mode:
                        try:

                            # sell for real if test mode is set to false
                            if not test_mode:
                                sell = client.create_order(symbol = symbol, side = 'SELL', type = 'MARKET', quantity = volume, recvWindow = "10000")


                            sendmsg(f"Sold {symbol} at {(float(last_price) - stored_price) / float(stored_price)*100}")
                            killSpam(symbol)
                            flag_update = True
                            # remove order from json file by not adding it

                        except Exception as exception:
                            wrong = traceback.format_exc(limit=None, chain=True)
                            sendmsg(wrong)

                        # store sold trades data
                        else:
                            if os.path.exists(executed_sells_file):
                                sold_coins = load_json(executed_sells_file)

                            else:
                                sold_coins = []

                            if not test_mode:
                                sold_coins.append(sell)
                            else:
                                sell = {
                                            'symbol':symbol,
                                            'price':last_price,
                                            'volume':volume,
                                            'time':datetime.timestamp(datetime.now()),
                                            'profit': float(last_price) - stored_price,
                                            'relative_profit': round((float(last_price) - stored_price) / stored_price*100, 3)
                                            }
                                sold_coins.append(sell)
                            save_json(executed_sells_file, sold_coins)

                    else:
                        not_sold_orders.append(coin)
                    if flag_update: save_json(executed_trades_file, not_sold_orders)
            time.sleep(0.2)
        except Exception as exception:       
            wrong = traceback.format_exc(limit=None, chain=True)
            sendmsg(wrong)


def main():

    if os.path.exists(file):
        existing_Anouncements = load_json(file)

    else:
        existing_Anouncements = get_Announcements()
        for announcement in existing_Anouncements:
            time_And_Pair = get_Pair_and_DateTime(announcement['code'])
            if time_And_Pair is not None:
                if time_And_Pair[0] >= datetime.utcnow()  and len(time_And_Pair[1]) > 0:
                    schedule_Order(time_And_Pair, announcement)
                    sendmsg(f'Found new announcement preparing schedule for: {time_And_Pair[1]}')
        save_json(file, existing_Anouncements)

    threading.Thread(target=check_Schedules, args=()).start()
    threading.Thread(target=sell, args=()).start()
    threading.Thread(target=executed_orders, args=()).start()
    
    while True:
        new_Anouncements = get_Announcements()
        
        for announcement in new_Anouncements:
            if not announcement in existing_Anouncements:
                time_And_Pair = get_Pair_and_DateTime(announcement['code'])
                if time_And_Pair is not None:
                    if time_And_Pair[0] >= datetime.utcnow() and len(time_And_Pair[1]) > 0 :
                        schedule_Order(time_And_Pair, announcement)
                        for pair in time_And_Pair[1]:
                            threading.Thread(target=place_Order_On_Time, args=(time_And_Pair[0], pair, threading.active_count() + 1)).start()
                            sendmsg(f'Found new announcement preparing schedule for {pair}')
                existing_Anouncements = load_json(file)
        
        threading.Thread(target=sendSpam, args=("sleep", f'Done checking announcements going to sleep for: {frequency} seconds&disable_notification=true')).start()
        threading.Thread(target=sendSpam, args=("ping", f'Current Average delay: {ping_binance()}&disable_notification=true')).start()
        time.sleep(frequency)


#TODO:
# posible integration with AWS lambda ping it time before the coin is listed so it can place a limit order a little bti more than opening price


if __name__ == '__main__':
    try:
        if not test_mode:
            sendmsg('Warning runnig it on live mode')
        sendmsg('starting')
        sendmsg(f'Aproximate delay: {ping_binance()}')
        main()
    except Exception as exception:
        wrong = traceback.format_exc(limit=None, chain=True)
        sendmsg(wrong)









#debuggin order
#{
#    "time": "2021-09-24 10:00:00",
#    "pairs": [
#        "DFUSDT",
#        "SYSUSDT"
#    ]
#}