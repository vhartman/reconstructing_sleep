import numpy as np
import matplotlib.pyplot as plt

import json
import codecs
from datetime import datetime, timedelta

import plot

def load_android_activity(path):
    with open(path) as f:
        data = json.load(f)

        # filter data
        timestamps = []
        for d in data:
            if 'Verwendet: Instagram' not in d['title'] and\
                'Verwendet: Google Chrome' not in d['title'] and\
                'Verwendet: WhatsApp' not in d['title'] and\
                'Verwendet: Spotify' not in d['title']:
                continue

            try:
                t = datetime.strptime(d['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                t = datetime.strptime(d['time'], "%Y-%m-%dT%H:%M:%SZ")

            if t.year >= 2018:
                timestamps.append(t)

        return timestamps

def load_activity(path):
    with open(path) as f:
        data = json.load(f)

        # filter data
        timestamps = []
        for d in data:
            try:
                t = datetime.strptime(d['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                t = datetime.strptime(d['time'], "%Y-%m-%dT%H:%M:%SZ")

            if t.year >= 2018:
                timestamps.append(t)

        return timestamps

def load_wa(path):
    def load(name):
        doc = []

        f = codecs.open(name, encoding='utf-8')
        for line in f:
            doc.append(str(line))

        return doc

    def to_list(f):
        txt = []
        for line in f:
            if len(line.split(",")[0]) == 8 and len(line.split("-")[0]) == 16:
                txt.append(line)
            else:
                txt[-1] = ' '.join([txt[-1], line])

        timestamps = []
        for line in txt:
            sender = line.split(':')[1].split("-")[-1].strip()

            if sender != 'Valentin':
                continue

            date_str = line.split('-')[0][:-1].strip()
            date = datetime.strptime(date_str, "%d.%m.%y, %H:%M")

            timestamps.append(date)

        return timestamps

    data = load(path)
    return to_list(data)

def extract_approx_sleep_from_ts(timestamps):
    timestamps = [t for t in timestamps if t >= datetime(2018, 9, 1)]
    diff = np.array(timestamps)[1:] - np.array(timestamps)[:-1]

    v_func = np.vectorize(lambda x: x.total_seconds())
    diff_sec = v_func(diff)

    lower_bound = 4
    sleep = {'duration': [], 'begin': [], 'end': []}
    awake = True
    sleep_start = None
    sleep_end = None
    for i in range(len(timestamps) - 10):
        if awake and (timestamps[i+1] - timestamps[i]).total_seconds() / 60 / 60 > lower_bound and\
           (sleep_end is None or (timestamps[i] - sleep_end).total_seconds() / 60 / 60 > 5):
            awake = False
            sleep_start = timestamps[i]
        
        if not awake and (timestamps[i+1] - timestamps[i]).total_seconds() / 60 < 60:
            awake = True

            sleep_end = timestamps[i]

            # filter out kilimanjaro-days
            if sleep_start >= datetime(2019, 9, 7) and sleep_start <= datetime(2019, 9, 13):
                continue

            sleep['duration'].append((sleep_end - sleep_start).total_seconds() / 60 / 60)
            sleep['begin'].append(sleep_start)
            sleep['end'].append(sleep_end)

    return sleep

def load_data(android, google, whatsapp):
    ts = []

    for name, path in android:
        t = load_android_activity(path)
        t = correct_for_daylightsavings(t)
        ts.append((name, t))

    for name, path in whatsapp:
        t = load_wa(path)
        ts.append((name, t))

    for name, path in google:
        t = load_activity(path)
        t = correct_for_daylightsavings(t)
        ts.append((name, t))

    return ts

def aggregate_and_sort_timestamps(named_timestamps):
    all_ts = []
    for name, t in named_timestamps:
        all_ts.extend(t)
    all_ts.sort()

    return all_ts

def correct_for_daylightsavings(ts):
    corr_ts = []

    for t in ts:
        if (t.month >= 4 or (t.day > 29 and t.month == 3)) and (t.month <= 9 or (t.month == 10 and t.day <= 25)):
            t_corr = t + timedelta(hours=1)
            corr_ts.append(t_corr)
        else:
            corr_ts.append(t)

    return corr_ts

def make_html():
    android = [('Android', "./full_google_export/Meine Aktivitäten/Android/MeineAktivitäten.json")]

    whatsapp = [('Whatsapp', "./chat.txt")]

    google = [('YouTube', "./full_google_export/YouTube/Verlauf/Wiedergabeverlauf.json"),
              ('GSearch', './full_google_export/Meine Aktivitäten/Google-Suche/MeineAktivitäten.json'),
              ('Chrome', './full_google_export/Meine Aktivitäten/Chrome/MeineAktivitäten.json'),
              ('Google Analytics', './full_google_export/Meine Aktivitäten/Google Analytics/MeineAktivitäten.json')]

    named_timestamps = load_data(android, google, whatsapp)
    all_ts = aggregate_and_sort_timestamps(named_timestamps)

    s = approx_sleep = extract_approx_sleep_from_ts(all_ts)
    plot.plot_trendline(s)

    plot.scatter_data(named_timestamps)

    approx_sleep = extract_approx_sleep_from_ts(
        [t for t in all_ts if t >= all_ts[-1] - timedelta(days=100)])
    plot.plot_stuff(approx_sleep)
    plot.ridge_wrapper(approx_sleep, "_recent")
    fig = plt.figure('distributions')
    fig.savefig('./out/recent_distr.png', bbox_inches='tight', transparent=True)
    plt.clf()

    time_slices = [['Verity Studios', (datetime(2018, 1, 9), datetime(2019, 4, 10))],
                   ['BCG Gamma', (datetime(2019, 4, 10), datetime(2019, 9, 1))],
                   ['PhD', (datetime(2019, 9, 1), datetime(2019, 12, 20))]]

    joy_plts = []
    for name, time_slice in time_slices:
        approx_sleep = extract_approx_sleep_from_ts(
            [t for t in all_ts if t >= time_slice[0] and t <= time_slice[1]])

        plot.plot_stuff(approx_sleep, name)
        plot.plot_lines(approx_sleep)

        filename = plot.ridge_wrapper(approx_sleep, name)
        joy_plts.append(filename)

    fig = plt.figure('distributions')
    fig.savefig("./out/dists.png", bbox_inches='tight', transparent=True)

    fig = plt.figure('lines')
    fig.savefig('./out/lines.png', bbox_inches='tight', transparent=True)

    # actually put everything into the html file
    f = open("./out/file.html",'w')

    wrapper = """<html>
    <head>
    <title>Your sleep-habits suck</title>
    <style type="text/css">figcaption {{font-size: 12.5px}}</style>
    </head>
    <body style="font: 400 14px/1.5 -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'">
    <div style="width:800px; margin-left: auto; margin-right: auto">
        <h1>Most recent sleep distribution</h1>
        <img style="width: 100%;margin:auto" src="recent_distr.png"">
        <figcaption>This plot shows the distributions for the wake-up and sleep times, and the sleep-duration for the most recent 100 days.</figcaption>
        
        <h2>Split up in days</h2>
        <img style="width: 100%;margin:auto" src="distr_day_joy_recent.png"">
        <figcaption>The same data as above (the most recent 100 days) is split up into weekdays.</figcaption>

        <h2>Evolution of sleeping time over the dataset</h2>
        <img style="width: 100%;margin:auto" src="trend.png"">
        <figcaption>Here, the data of the whole time is shown together with a trendline to help identify changes in sleep-behaviour that might be interesting to look at more closely.</figcaption>

        <h1>Comparing the specified time-slices</h1>
        <img style="width: 100%;margin:auto" src="dists.png"">
        <figcaption>We first compare the different timeslices all together on a weekend vs. weekday basis.</figcaption>

        <h2>Day-level plots for each timeslice</h1>
        In the following, all timeslices are split up into days to have a closer look at.

        {0}

        <h1>Data overview</h1>
        <img style="width: 100%;margin:auto" src="scatter.png"">
        <figcaption>All datapoints</figcaption>
        <img style="width: 100%;margin:auto" src="lines.png"">
        <figcaption>The computed sleep-durations between the sleep-and wakeup indicators.</figcaption>
    </div>
    </body>
    </html>""".format(
    '\n'.join(['<img style="width: 100%;margin:auto" src="{}">'.format(filename) for filename in joy_plts]))

    f.write(wrapper)
    f.close()

def create_plots_for_post():
    android = [('Android', "./full_google_export/Meine Aktivitäten/Android/MeineAktivitäten.json")]

    whatsapp = [('Whatsapp', "./chat.txt")]

    google = [('YouTube', "./full_google_export/YouTube/Verlauf/Wiedergabeverlauf.json"),
              ('GSearch', './full_google_export/Meine Aktivitäten/Google-Suche/MeineAktivitäten.json'),
              ('Chrome', './full_google_export/Meine Aktivitäten/Chrome/MeineAktivitäten.json'),
              ('Google Analytics', './full_google_export/Meine Aktivitäten/Google Analytics/MeineAktivitäten.json')]

    named_timestamps = load_data(android, google, whatsapp)
    all_ts = aggregate_and_sort_timestamps(named_timestamps)

    s = approx_sleep = extract_approx_sleep_from_ts(all_ts)
    plot.plot_trendline(s)

    plot.scatter_data(named_timestamps)

    time_slices = [['Verity Studios', (datetime(2018, 1, 9), datetime(2019, 4, 10))],
                   ['BCG Gamma', (datetime(2019, 4, 10), datetime(2019, 9, 1))],
                   ['PhD', (datetime(2019, 9, 1), datetime(2019, 12, 20))]]

    # extract_approx_sleep(all_ts)
    for name, time_slice in time_slices:
        print(name)
        approx_sleep = extract_approx_sleep_from_ts(
            [t for t in all_ts if t >= time_slice[0] and t <= time_slice[1]])

        plot.plot_stuff(approx_sleep, name)
        plot.plot_lines(approx_sleep)

        plot.ridge_wrapper(approx_sleep, name)

    fig = plt.figure('distributions')
    fig.savefig("./out/dists.png", bbox_inches='tight', transparent=True)

    fig = plt.figure('lines')
    fig.savefig('./out/lines.png', bbox_inches='tight', transparent=True)

    plt.show()

if __name__ == "__main__":
    #create_plots_for_post()
    make_html()
