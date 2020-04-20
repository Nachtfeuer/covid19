"""tool visualize"""
# Copyright (c) 2020 Thomas Lehmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
# to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.import os
import os
import requests
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

always = True
url = "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv"

if not os.path.isfile("covid19.csv") or always:
    response = requests.get(url)
    with open('covid19.csv', 'wb') as stream:
        stream.write(response.content)

df = pd.read_csv('covid19.csv')
# filter for Germany
df_germany = df[df.countriesAndTerritories.eq('Germany')]
# sort by date ascending
df_germany = df_germany.sort_values(by=['year', 'month', 'day'])
df_germany = df_germany.reset_index(drop=True)

print(df_germany)

fig, main_axes = plt.subplots(nrows=2, ncols=1, sharex=True)
fig.suptitle(url, fontsize=8)

# adjusting figure to show in resolution of 1024x768 pixel
DPI = fig.get_dpi()
fig.set_size_inches(1024/float(DPI), 768/float(DPI))

title = 'Corona Infizierte in Deutschland (Insgesamt: %d)' % df_germany['cases'].sum()
axes = df_germany.plot(x='dateRep', y='cases', title=title,
                       ax=main_axes[0],
                       kind='line', grid=True, color='#008000', legend=False)
axes.set_xlabel('Datum')
axes.set_ylabel('Infizierte pro Tag')

# square polynomial fit for Corona cases
x = np.arange(df_germany['dateRep'].values.flatten().shape[0])
p = np.poly1d(np.polyfit(x, df_germany['cases'].values.flatten(), 4))
main_axes[0].plot(x, p(x), linestyle='dashed', linewidth=0.75, color='#800000')

title = 'Corona Tote in Deutschland (Insgesamt: %d)' % df_germany['deaths'].sum()
axes = df_germany.plot(x='dateRep', y='deaths', title=title,
                       ax=main_axes[1],
                       kind='line', grid=True, color='#008000', legend=False)
axes.set_xlabel('Datum')
axes.set_ylabel('Tote pro Tag')

# square polynomial fit for Corona deaths
p = np.poly1d(np.polyfit(x, df_germany['deaths'].values.flatten(), 4))
main_axes[1].plot(x, p(x), linestyle='dashed', linewidth=0.75, color='#800000')

# export as png format
plt.savefig('covid19.png', format='png')
# show the window with the result
plt.show()
