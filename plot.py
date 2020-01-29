import numpy as np
import matplotlib.pyplot as plt

from scipy import stats

def aggregate_data_for_days(days, data):
    duration = []
    sleep = []
    wake = []

    for i in range(len(data['end'])):
        if data['end'][i].weekday() in days:
            duration.append(data['duration'][i])
            wake.append(data['end'][i].hour + data['end'][i].minute/60)
        
        if data['end'][i].weekday() in list((np.array(days)+1)%7):
            sleep.append(data['begin'][i].hour + data['begin'][i].minute/60)

    return duration, sleep, wake

def approx_distribution(x, data, bw=None, offset=0):
    data = np.array(data)
    data_off = (data + offset) % 24

    gaussian_pdf = stats.gaussian_kde(data_off, bw)

    avg = (np.mean((data + offset) % 24) - offset) % 24
    std = (np.var((data + offset) % 24) - offset) % 24

    return gaussian_pdf(x), avg, std

def ridgeplot(x, data, ax=None, labels=None):
    if ax is None:
        fig = plt.figure("d")
        ax = fig.add_subplot(1, 1, 1)
    
    avgs = []

    for i, distr in enumerate(data):
        avg = np.average(x, axis=0, weights=distr)
        avgs.append(avg)

    overall_avg = np.mean(avgs)

    for i, distr in enumerate(data):
        avg = np.average(x, axis=0, weights=distr)

        g = max([0, min([.466-(avg-overall_avg)/5, 1])])
        b = max([0, min([.7-(avg-overall_avg)/5, 1])])
        c = np.tile((.121, g, b, .9), (len(x), 1))

        y_off = (len(data) - i) / 9.

        ax.fill_between(x, distr+y_off, x*0+y_off, facecolor=c, edgecolor='black', linewidth=0.5)

        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)

        ax.xaxis.grid()
        ax.set_xticks([5, 7, 9, 11])

        ax.set_yticks(np.arange(1/9, 7/9.+1e-3, 1/9))
        if labels is not None:
            ax.set_yticklabels(labels[::-1])

    ax.plot(avgs[::-1], np.arange(1/9, 7/9.+1e-3, 1/9) + 1/18, '--x', color='black', label='Average')

def plot_distribution(x, distr, avg, ax, offset=0, l=False, y_off=0, disp_avg=False, label=""):
    if l:
        p = ax.plot(x-offset, distr, label=label)
    else:
        p = ax.plot(x-offset, distr)
    
    if disp_avg:
        ax.plot([(avg+offset)%24-offset, (avg+offset)%24-offset], [0+y_off, .5+y_off], '--', color=p[0].get_color(), linewidth=1)

def plot_stuff(sleep, label=''):
    x_dur = np.arange(2, 14, 0.1)
    x_wake = np.arange(2, 15, 0.1)
    x_sleep = np.arange(5, 15, 0.1)

    fig = plt.figure("distributions", figsize=(15, 7.5))

    splits = [[0, 1, 2, 3, 4],[5, 6]]
    labels = ['Week', 'Weekend']

    sharex = []
    
    for i, split in enumerate(splits):
        dur, slp, wake = aggregate_data_for_days(split, sleep)

        if i == 0:
            ax = fig.add_subplot(len(splits), 3, i*3+1)
            ax.set_title("Wake-up")
            sharex.append(ax)
        else:
            ax = fig.add_subplot(len(splits), 3, i*3+1, sharex=sharex[0])

        ax.set_ylabel(labels[i])
        ax.set_yticks([])

        ax.set_xticks([5, 7, 9, 11])

        #ax.hist(wake, bins=50, range=(0, 24), density=True, alpha=0.5)
        d, avg, _ = approx_distribution(x_wake, wake, bw=0.5)
        plot_distribution(x_wake, d, avg, ax, disp_avg=True, label=label)

        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.xaxis.grid()

        if i!=len(splits)-1:
            plt.setp(ax.get_xticklabels(), visible=False)

        if i == 0:
            ax = fig.add_subplot(len(splits), 3, i*3+2)
            ax.set_title("Sleep")
            sharex.append(ax)
        else:
            ax = fig.add_subplot(len(splits), 3, i*3+2, sharex=sharex[1])

        #ax.hist(slp, bins=50, range=(0, 24), density=True, alpha=0.5)
        d, avg, _ = approx_distribution(x_sleep, slp, bw=0.5, offset=10)
        plot_distribution(x_sleep, d, avg, ax, disp_avg=True, offset=10, label=label)

        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.xaxis.grid()

        ax.set_xticks([-3, -1, 1, 3])
        ax.set_xticklabels([21, 23, 1, 3])

        ax.set_yticks([])

        if i!=len(splits)-1:
            plt.setp(ax.get_xticklabels(), visible=False)

        if i == 0:
            ax = fig.add_subplot(len(splits), 3, i*3+3)
            ax.set_title("Duration")
            sharex.append(ax)
        else:
            ax = fig.add_subplot(len(splits), 3, i*3+3, sharex=sharex[2])

        ax.set_xticks([5, 7, 9, 11])
        ax.set_yticks([])

        #ax.hist(dur, bins=50, range=(0, 14), density=True, alpha=0.5)
        d, avg, _ = approx_distribution(x_dur, dur, bw=0.5)
        plot_distribution(x_dur, d, avg, ax, disp_avg=True, l=True, label=label)

        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.xaxis.grid()

        if i!=len(splits)-1:
            plt.setp(ax.get_xticklabels(), visible=False)

        ax.legend()

def plot_lines(sleep):
    fig = plt.figure("lines", figsize=(15, 7.5))
    ax = fig.add_subplot(1,1,1)
    plt_timestamps(ax, sleep['begin'], '')
    plt_timestamps(ax, sleep['end'], '')

    for b, e in zip(sleep['begin'], sleep['end']):
        if b.day != e.day:
            ax.plot([b, b], [b.hour + b.minute/60, 24], color='tab:blue')
            ax.plot([e, e], [0, e.hour + e.minute/60], color='tab:blue')
        else:
            ax.plot([b, e], [b.hour + b.minute/60, e.hour + e.minute/60], color='tab:blue')

    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)

    ax.set_ylim([0, 24])

def plt_timestamps(ax, timestamps, label):
    mins = []
    hours = []
    for t in timestamps:
        mins.append(t.minute)
        hours.append(t.hour)

    ax.scatter(timestamps, np.array(hours) + np.array(mins)/60., s=3, label=label)

def scatter_data(named_timestamps):
    fig = plt.figure(figsize=(15, 7.5))
    ax = fig.add_subplot(1,1,1)

    for name, t in named_timestamps:
        plt_timestamps(ax, t, name)

    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.legend()

    fig.savefig("./out/scatter.png", bbox_inches='tight', transparent=True)

def ridge_wrapper(d, name=''):
    x = np.arange(2, 14, 0.1)
    x_slp = np.arange(5, 15, 0.1)

    fig = plt.figure('Day distr'+name, figsize=(15, 10))
    titles = ['Wake-up', 'Sleep', 'Duration']
    for i in [2, 1, 0]:
        if i == 2:
            ax = fig.add_subplot(1, 3, i+1)
            ax0 = ax
        else:
            ax = fig.add_subplot(1, 3, i+1, sharey=ax0)

        ax.set_title(titles[i])

        off = 0
        x_tmp = x
        if i == 1:
            x_tmp = x_slp
            off = 10

        if i!=0:
            plt.setp(ax.get_yticklabels(), visible=False)

        tmp = [approx_distribution(x_tmp, aggregate_data_for_days([j], d)[i], offset=off)[0] for j in np.arange(0, 7, 1)]
        ridgeplot(x_tmp-off, tmp, ax=ax, labels=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

        ax.set_ylim([0, 1.3])

        if i == 1:
            ax.set_xticks([-3, -1, 1, 3])
            ax.set_xticklabels([21, 23, 1, 3])

        if i==2:
            ax.legend()

    filename = "distr_day_joy_"+name+".png".replace(' ', '_')
    fig.savefig('./out/'+ filename, bbox_inches='tight', transparent=True)

    return filename

def plot_trendline(s):
    def ma(x, N=11):
        return np.convolve(x, np.ones((N,))/N, mode='same')

    def tmp(data, days):
        w = []
        d = []

        for i in range(len(data['end'])):
            if data['end'][i].weekday() in days:
                d.append(data['duration'][i])
                w.append(data['end'][i])
        return w, d

    # fig = plt.figure(figsize=(15, 7.5))
    # ax = fig.add_subplot(1,1,1)

    # w, d = tmp(s, [0, 1, 2, 3, 4])
    # d = np.reshape(d, (-1, 5))
    # w_we, d_we = tmp(s, [5, 6])
    # d_we = np.reshape(d_we[:-1], (-1, 2))

    # d_con = np.concatenate((d, d_we), axis=1)
    # d_con = np.clip(d_con, 5, 10)
    # cax = ax.imshow(d_con.T, cmap="PiYG")
    # fig.colorbar(cax)

    fig = plt.figure(figsize=(15, 7.5))
    ax = fig.add_subplot(1,1,1)

    splits = [[0,1,2, 3, 4], [5, 6]]
    label = ['Weekday', 'Weekend']
    color = ['tab:blue', 'tab:orange']
    for i, days in enumerate(splits):
        N = 11
        w, d = tmp(s, days)
        w = w[N:-N]
        d = ma(d, N)[N:-N]
        ax.scatter(w, d, label=label[i], color=color[i])

        N = 31
        w, d = tmp(s, days)
        w = w[int(N/2):-int(N/2)]
        d = ma(d, N)[int(N/2):-int(N/2)]
        ax.plot(w, d, '--', color=color[i], linewidth=1)

    ax.legend()
    ax.set_ylabel('Sleep duration [h]')

    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)

    fig.savefig("./out/trend.png", bbox_inches='tight', transparent=True)
