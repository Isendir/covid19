###########################################################################
#
#    trend.py - Analyse data of the spread of the COVID19
#    usage: python3 trend.py [name of the country] [minimum number of ills]
#    Copyright (C) 2020 giovanni.organtini@uniroma1.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###########################################################################
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import timedelta as td
import datetime as dt
from scipy.optimize import curve_fit
import wget
import ssl
import sys

# You can download the data from the following URL. Data are expected to be organised as
# in the given CSV file. 

ssl._create_default_https_context = ssl._create_unverified_context
url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'

# comment the following line to avoid downloading the file from the Internet
#filename = wget.download(url)
# comment to download the file from the Internet
filename = 'time_series_19-covid-Confirmed.csv'

# The model function
def fun(x, a, b):
    return a*np.exp(x/b)

# A function to make nice plots
def myplot(x, y, ylabel, fname='output.png'):
    plt.figure(figsize=(12,7))
    plt.plot(x, y, 'o')
    plt.xticks(rotation=45)
    plt.ylabel(ylabel)
    plt.savefig(fname)
    plt.show()

# Open the data file and read it
f = open(filename, 'r')

w = pd.read_csv(filename)
data = w.values.tolist()
head = [dt.datetime.strptime(x, '%m/%d/%y') for x in w.columns[4:]]
i = 0;

# Select only data belonging to a given country as specified in column 1
country = sys.argv[1]
while data[i][1] != country:
    i += 1
Nill = data[i][4:]

# Use only data with Nill > threshold. By default the threshold is 4
i = 0
min_val = 4
if (len(sys.argv) > 2):
    min_val = int(sys.argv[2])
print('Using only data with Nill > {}'.format(min_val))
while (Nill[i] < min_val):
    i += 1

Nill = Nill[i:]
head  = head[i:]

# Compute the logarithm of the data
lNill = [np.log(x) for x in Nill]

# Do plots of data and their logarithm vs time
myplot(head, Nill, 'N', 'NvsT.png')
myplot(head, lNill, 'log(N)', 'logNvsT.png')

# A function to perform a fit
def fit(y, n, m=-1):
    if m < 0:
        m = len(y)-1
    print('Fitting points from {} to {}'.format(n, m))
    Nr = y[n:m]
    xr = np.arange(n,m)
    dNr = [np.sqrt(x) for x in Nr]
    p, cov = curve_fit(fun, xr, Nr, sigma=dNr)
    s0 = np.sqrt(cov[0][0])
    s1 = np.sqrt(cov[1][1])
    return p[0], p[1], s0, s1

# Fit the last data with the model
A, tau, dA, dtau = fit(Nill, len(Nill)-9)
print('Fit done: tau = {} +- {}'.format(tau, dtau))
print('            A = {} +- {}'.format(A, dA))

# A function to make a nice plot
def myplotfit(plt, x, y, p0, p1, s0, s1, legendPosition=0, legend=None):
    plt.xticks(rotation=45)
    plt.plot(x, np.log(y), 'o')
    xr = range(len(x))
    if legend != None:
        ymin, ymax = plt.ylim()
        plt.annotate(legend, (0.1, legendPosition), xycoords='axes fraction')
    s1 = p0*np.exp(xr/p1)*xr/p1**2*s1
    s0 = np.exp(xr/p1)*s0
    s  = np.sqrt(s1**2+s0**2)
    f0 = fun(xr, p0, p1)
    f1 = fun(xr, p0, p1)+s
    f2 = fun(xr, p0, p1)-s
    plt.plot(x, np.log(f0))
    plt.fill_between(x, np.log(f1), np.log(f2), alpha=0.25)

# Create a plot and show data with the model superimposed
plt.figure(figsize=(12,7))
myplotfit(plt, head, Nill, A, tau, dA, dtau, 0, 'Fit last 10 points')
plt.show()

# Fit a portion of the data iteratively
xmax = len(head) - 1
xmin = xmax - 4
plt.figure(figsize=(12,7))
plt.title(country)
legendPos = 0.9
taudata = [0]*len(head)
while xmin > 0:
    # Fit the given portion of data
    A, tau, dA, dtau = fit(Nill, xmin, xmax)
    taudata[xmin] = tau
    print('Fit done: tau = {} +- {} ({})'.format(tau, dtau, dtau/tau))
    print('            A = {} +- {} ({})'.format(A, dA, dA/A))
    # Add the model to the plot
    label = 'Fit from ' + str(xmin) + ' to ' + str(xmax) + ': $\\tau = {:.2f}$ d'.format(tau) 
    myplotfit(plt, head, Nill, A, tau, dA, dtau, legendPos, label)
    xmax -= 4
    xmin = xmax - 4
    legendPos -= 0.1

# Show the plot with the various models superimposed
plt.savefig('multimodel.png')
plt.show()

# Make a plot of the evolution of the characteristic time
plt.figure(figsize=(12,7))
plt.plot(head, taudata, 'o')
plt.ylim(bottom = 0.1)
plt.xticks(rotation=45)
plt.ylabel('Characteristic time [d]')
plt.show()