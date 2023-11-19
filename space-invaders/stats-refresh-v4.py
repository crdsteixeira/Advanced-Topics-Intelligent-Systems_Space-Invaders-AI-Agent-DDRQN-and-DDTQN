import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.ndimage import uniform_filter1d
import time
import warnings

def moving_average(x, w):
    avg_xx = np.convolve(x, np.ones(w), 'valid') / w
    scores_xx_len = len(avg_xx)
    return avg_xx, scores_xx_len, range(w, w + scores_xx_len, 1)

def running_mean(x, w):
    avg_xx = uniform_filter1d(x, size=w, mode='constant', cval=np.mean(x))
    scores_xx_len = len(avg_xx)
    return avg_xx, scores_xx_len, range(0, scores_xx_len, 1)

def batch_mean(x, w):
    scores_xx_len = len(x) - (len(x) % w)
    scores_xx = x[0:scores_xx_len]
    #scores_xx = scores_xx.reshape(-1, w)
    scores_xx = np.array(np.array_split(scores_xx, len(scores_xx) // w, axis=0))
    avg_xx = np.mean(scores_xx, axis=1)
    scores_xx_len = len(avg_xx)
    x_ticks = range(w, (scores_xx_len + 1) * w, w)
    return avg_xx, scores_xx_len, x_ticks

def weighted_mean(x, w):
    w_x = (1.0 - scores[:, 1]) * scores[:, 0]
    return running_mean(w_x, window)

window = 1

plt.style.use('dark_background')
# to run GUI event loop
plt.ion()

# here we are creating sub plots
figure, ax = plt.subplots(figsize=(7, 5))
line_v, = ax.plot([0], [0])
line_p, = ax.plot([0], [0])

# setting x-axis label and y-axis label
plt.xlabel("Episode (Game number)")
plt.ylabel("Score")

while True:
    time.sleep(2)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            scores = np.loadtxt('stats_RNN.txt')
        scores = scores.reshape(-1, 3)
    except Exception as e:
        continue

    if not scores.shape[0] > 0:
        continue

    # setting title
    epsilon = scores[-1, 1]
    plt.title(f'Average score (running mean {window} episodes, epsilon {epsilon})'.format(window, epsilon), fontsize=12)

    #avg_xx, scores_xx_len, x_ticks = moving_average(scores[:, 0], window)
    avg_xx, scores_xx_len, x_ticks = running_mean(scores[:, 2], window)
    #avg_xx, scores_xx_len, x_ticks = batch_mean(scores[:, 0], window)
    #avg_xx, scores_xx_len, x_ticks = weighted_mean(scores, window)
    print(scores.shape, scores_xx_len, np.mean(scores[:, 0]), scores[-1, 1], scores[-1, 0], scores[-1, 2])
    #z = np.polyfit(range(len(scores)), scores[:, 0], 1)
    z = np.polyfit(range(scores_xx_len), avg_xx, 1)
    p = np.poly1d(z)

    # updating data values
    line_v.set_xdata(x_ticks)
    line_v.set_ydata(avg_xx)
    line_p.set_xdata(x_ticks)
    line_p.set_ydata(p(range(len(avg_xx))))
    ax.autoscale_view()
    ax.set_ylim([0.50 * np.min(avg_xx), 1.50 * np.max(avg_xx)])
    ax.set_xlim([0, int(1.05 * np.max(x_ticks))])
    #ax_xticks = ax.get_xticks().astype(int)
    #print(ax_xticks)
    #ax.set_xticks(ax_xticks)
    #ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.tick_params(axis='x', labelrotation=90)

    # drawing updated values
    figure.canvas.draw()

    # This will run the GUI event
    # loop until all UI events
    # currently waiting have been processed
    figure.canvas.flush_events()
