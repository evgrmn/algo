import pandas as pd
from datetime import datetime
from matplotlib.figure import Figure
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import glob, os
from sys import argv
root = Tk()
root.title('')
tm = datetime.utcnow()
start_date, end_date = int(argv[1]), int(argv[2])
front = 10          # candeles number
visual = argv[3]    # yes - display 
d = {}
def refresh():
    global step, play, last_date, max_step
    if play:
        if play == 'animate':
            step += 1
        elif play == 'playback':
            step -= 1
            play = ''
            if step < 0:
                step = 0
        elif play == 'play':
            step += 1
            play = ''
        if step < len(d['date'])-1 and step >= 0:
            if step > max_step:
                robot()
            candles.cla()
            begin = step - front
            end = step + 1
            if step < front:
                begin = 0
            sliced = data.iloc[begin:end]
            x_lebels = sliced['time'].tolist()
            up = sliced[sliced['close'] >= sliced['open']]
            down = sliced[sliced['close'] < sliced['open']]              
            candles.bar(up.index, up['close'] - up['open'], width, bottom = up['open'] , color = col1)
            candles.bar(up.index, up['hi'] - up['lo'], width2, bottom = up['lo'] , color = col1) 
            candles.bar(down.index, down['close'] - down['open'], width, bottom = down['open'] ,color = col2)
            candles.bar(down.index, down['hi'] - down['lo'], width2, bottom = down['lo'], color = col2)
            def p(l):
                a = []
                for i in l:
                    a.append(i['price'])
                    if len(i['lots']) == 2:
                        a.append(i['price'])
                return a
            s = p(orders[-1])
            b = p(orders[1])
            if step > max_step:
                b_list.append(b)
                s_list.append(s)
            b_actual = b_list[step]
            s_actual = s_list[step]
            ac = (max(sliced['hi']) + min(sliced['lo'])) / 400
            candles.scatter([end - 1] * len(s_actual), s_actual)
            candles.scatter([end - 1] * len(b_actual), b_actual) #1 / len(sliced)
            if s_actual:
                e_ask = s_actual[-1] + ac
                candles.text(end - 1, e_ask, len(s_actual), size=13, bbox=dict(boxstyle="square", ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8),))
            if b_actual:
                e_bid =b_actual[-1] - ac * 1.5
                candles.text(end - 1, e_bid, len(b_actual), size=13, bbox=dict(boxstyle="square", ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8),))
            candles.set_ylabel('Price')
            if maxcapital:
                candles.set_title('Date: ' + str(sliced['date'].iloc[0])[:10] + '\n' +
                                  'Balance: ' + str(round(sumbal, 1)) + 'Btc' + '\n' + 
                                  'Result: ' + str(round(result, 2)) + 'Btc' + '\n' +
                                  'Maximum used funds: ' + str(round(maxcapital, 1)) + 'Btc' + '\n' +
                                  'Days: ' + str(days) + '\n' +
                                  'Annual return: ' + str(round(result / abs(maxcapital) / days * 365 * 100, 2)) + '%'
                                  , loc='left', y=0.4, x=1.1)            
            if d['date'][step] > last_date:
                last_date = d['date'][step]
                xs[0] = xs[1]
                ys[0] = ys[1]
                xs[1] = d['date'][step]
                ys[1] = result
                plotting.plot(xs, ys, linewidth = 3.0, color='tab:blue')
                plotting.set_ylabel('Result, Btc')          
            candles.set_xticks(sliced.index, minor=False)
            candles.set_xticklabels(x_lebels)
            candles.tick_params(labelrotation = 45)
            canvas.draw()
            if step > max_step:
                max_step = step
    root.after(1, refresh)
def key_pressed(event):
    global play
    if event.char == '\x1b':
        exit(1)
    elif event.keycode == 65 and play:
        play = ''
    elif event.keycode == 65 and not play:
        play = 'animate'
    elif event.keycode == 113:
        play = 'playback' 
    elif event.keycode == 114:
        play = 'play'
        
def place_orders(direction, del_lot, new_lot):
    if len(orders[direction][-1]['lots']) == 1:
        sum_orders[direction][0] -= orders[direction][-1]['lots'][0] / orders[direction][-1]['price']
        orders[direction][-1]['lots'].append(new_lot)
        orders[direction][-1]['price'] = price[direction]
        sum_orders[direction][0] += new_lot / price[direction]; sum_orders[direction][0] += orders[direction][-1]['lots'][0] / price[direction]
    else:
        sum_orders[direction][0] -= orders[direction][-1]['lots'][0] / orders[direction][-1]['price']
        orders[direction][-1]['lots'].pop(0)
        orders[direction].append({'price': price[direction], 'lots': [del_lot, new_lot]})
        sum_orders[direction][0] += new_lot / price[direction]; sum_orders[direction][0] += orders[direction][-1]['lots'][0] / price[direction]
    orders[-direction].append({'price': price[-direction], 'lots': [new_lot]})
    sum_orders[-direction][0] += new_lot / price[-direction]
    sum_orders[-direction][1] += 1
    sum_orders[direction][1] += 1
    orders[-1] = sorted(orders[-1], key = lambda p: p['price'])
    orders[1] = sorted(orders[1], key = lambda p: p['price'], reverse = True) 
         
def calculate(direction, price, lots):
    global sumvolume, comiss, maxbal, sumlots, sumcontracts
    while lots:
        sumlots += direction * lots[0]
        sumvolume += (direction * lots[0]) / price
        comiss += lots[0] / price * 0.0001
        sumcontracts += lots[0]
        sum_orders[direction][0] -= lots[0] / price
        sum_orders[direction][1] -= 1
        lots.pop(0)

def robot():
    global funding, maxprofit, drawdown, maxcapital, sumbal, result, averaging, days
    sumbal = sumlots / d['bid'][step]
    if d['fund'][step] != d['fund'][step + 1]:
        funding += -d['fund'][step] * sumbal / 100
    result = sumvolume - sumlots / d['bid'][step] + comiss + funding
    sum_sell = abs(sumbal - sum_orders[-1][0])
    sum_buy = abs(sumbal + sum_orders[1][0])
    sum_buysell = sum_buy
    if sum_sell > sum_buysell:
        sum_buysell = sum_sell
    if result > maxprofit:
        maxprofit = result
        drawdown = 0
    if maxprofit - result > drawdown:
        drawdown = maxprofit - result
    capital = drawdown + sum_buysell
    if capital > maxcapital:
        maxcapital = capital
    if d['date'][step] != d['date'][step + 1]:
        f.write(str(d['date'][step])[:10] + ';' + str(round(result, 3)) + '\n')
        days += (d['date'][step + 1] - d['date'][step]).days
    if averaging == 1:
        if orders[1]: 
            if d['ask'][step] > d['ask'][step - 1]:
                t = 1 / d['ask'][step - 10] - 1 / d['ask'][step]
                new_lot = round(d['bid'][step - 1] / 100) * 100
                del_lot = orders[1][-1]['lots'][0]
                volume = new_lot + del_lot
                price[1] = volume / (del_lot / orders[1][0]['price'] + 1)
                price[-1] = d['ask'][step] + d['ask'][step] / 100# + d['ask'][step] / 100
                if sum_orders[1][1] > sum_orders[-1][1]:
                    price[-1] = round(round(price[-1]/ precise) * precise, 1)
                price[1] = round(round(price[1]/ precise) * precise, 1)          
                place_orders(averaging, del_lot, new_lot)
    elif averaging == -1:
        if orders[-1]:
            if d['bid'][step] < d['bid'][step - 1]:
                t = 1 / d['bid'][step] - 1 / d['bid'][step - 1]
                new_lot = round(d['ask'][step - 1] / 100) * 100
                del_lot = orders[-1][-1]['lots'][0]
                volume = new_lot + del_lot
                price[-1] = volume / (del_lot / orders[-1][0]['price'] + 1)
                price[1] = d['bid'][step] - d['bid'][step] / 100# - d['bid'][step] / 100
                if sum_orders[1][1] < sum_orders[-1][1]:
                    price[1] = round(round(price[1]/ precise) * precise, 1)
                price[-1] = round(round(price[-1]/ precise) * precise, 1)
                place_orders(averaging, del_lot, new_lot)
    averaging = 0
    if not orders[-1] and not orders[1]:
        new_lot = round(d['bid'][step] / 100) * 100
        orders[-1].append({'price': d['ask'][step], 'lots': [new_lot]})
        sum_orders[-1][0] += d['bid'][step] / d['ask'][step]
        orders[1].append({'price': d['bid'][step], 'lots': [new_lot]})
        sum_orders[1][0] += 1
        orders[-1] = sorted(orders[-1], key = lambda p: p['price'])
        orders[1] = sorted(orders[1], key = lambda p: p['price'], reverse = True)
        sum_orders[1][1] += 1
        sum_orders[-1][1] += 1
    elif orders[-1] and not orders[1]:
        averaging = -1
    elif not orders[-1] and orders[1]:
        averaging = 1     
    elif orders[-1] and orders[1]:
        distans_buy = orders[1][-1]['lots'][0] / orders[1][-1]['price'] - orders[1][-1]['lots'][0] / d['bid'][step]
        distans_sell = orders[-1][-1]['lots'][0] / d['ask'][step] - orders[-1][-1]['lots'][0] / orders[-1][-1]['price']  
        if distans_buy > distans_sell:
            averaging = 1
        else:
            averaging = -1
    while orders[-1]:
        if d['hi'][step] >= orders[-1][0]['price']:
            calculate(-1, orders[-1][0]['price'], orders[-1][0]['lots'])
            orders[-1].pop(0)
        else:
            break
    while orders[1]:
        if d['lo'][step] <= orders[1][0]['price']:
            calculate(1, orders[1][0]['price'], orders[1][0]['lots'])
            orders[1].pop(0)
        else:
            break
sum_results = 0
num = 0     
os.chdir("data")        
for filename in glob.glob("*.txt"):
    print(filename)
    f = open('res/'+filename+'.res', 'w')
    f = open('res/'+filename+'.res', 'a')
    orders = {1: [], -1: []}
    sum_orders = {1: [0, 0], -1: [0, 0]}
    price = {1: 0, -1: 0}
    result = 0
    sumlots = 0
    sumvolume = 0
    comiss = 0
    funding = 0
    drawdown = 0
    maxcapital = 0
    maxprofit = 0
    averaging = 0
    sumcontracts = 0
    precise = 0.5
    days = 1
    b_list, s_list = [], []
    data = pd.read_csv(filename, sep=';')
    try:
        del data['none']
    except:
        pass
    data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    data['open'] = (data['bid'] + data['ask']) / 2
    data['close'] = data['open'].shift(-1)
    data.dropna(inplace = True)
    data = data.reset_index(drop=True)
    data['time'] = data['time'].astype(str)
    data['time'] = data['time'].apply(lambda x: '0' * (6 - len(x)) + x)
    data['time'] = data['time'].str[:2] + ':' + data['time'].str[2:4] + ':' + data['time'].str[4:6]
    data['datetime'] = pd.to_datetime(data['date'], format='%y%m%d')
    data['date'] = pd.to_datetime(data['date'], format='%y%m%d')
    for x in data:
        d[x] = data[x].to_list()
    day_start = 0
    xs = [d['date'][0], d['date'][0]]
    ys = [0, 0]
    last_date = d['date'][0]
    if visual == 'yes':
        root.bind("<Key>",key_pressed)
        step = -1
        max_step = -1
        width2 = .1
        col1 = 'green'
        col2 = 'red'
        play = 'animate'        
        fig = Figure(figsize = (9.25, 8), dpi = 90)        
        left, width = .25, .5
        bottom, height = .25, .5
        fig.text(0.82, 0.03, 'forth →', size=13, bbox=dict(boxstyle="square", ec='whitesmoke', fc='whitesmoke'))
        fig.text(0.15, 0.03, 'back ←', size=13, bbox=dict(boxstyle="square", ec='whitesmoke', fc='whitesmoke'))
        fig.text(0.43, 0.03, 'stop/play Spacebar', size=13, bbox=dict(boxstyle="square", ec='whitesmoke', fc='whitesmoke'))
        fig.suptitle('BitMEX XBTUSD ' + str(start_date) + '-' + str(end_date), fontsize=16)
        candles = fig.add_subplot(5, 3, (1, 5), facecolor = 'whitesmoke')
        plotting = fig.add_subplot(5, 1, (3, 15), facecolor = 'whitesmoke', visible = 'x')
        fig.subplots_adjust(hspace=1)
        canvas = FigureCanvasTkAgg(fig, master = root)  
        canvas.draw()  
        canvas.get_tk_widget().pack()
        refresh_var = root.after_idle(refresh)
        mainloop()
    else:
        for step in range(1, len(d['date']) - 1):
            robot()
        f.close()
        print(str(d['date'][step])[:10], '\nResult\t\t\t', round(result, 3), 'Btc\nFees\t\t\t', round(comiss, 5), 'Btc\nFunding\t\t\t', round(funding, 5), 'Btc\nMaximum used funds\t', round(maxcapital, 2), 'Btc\nContracts total\t\t', sumcontracts, 'Usd\nDays\t\t\t', days)
        print('Annual return\t\t', round(result / abs(maxcapital) / days * 365 * 100, 2), '%')
        
