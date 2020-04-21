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
import sys
import os
import platform
import logging
import requests
import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def initialize_logging():
    """Initializing the logging (file and console)"""
    format = '%(asctime)s - %(levelname)s - %(message)s'
    # file based logging
    logging.basicConfig(filename='visualize.log', level=logging.INFO, format=format)
    # adding console based logging
    consoleLogger = logging.StreamHandler()
    consoleLogger.setFormatter(logging.Formatter(format))
    logging.getLogger().addHandler(consoleLogger)
    # basic information at beginning (Python and platform)
    logging.info("Python %s", sys.version)
    logging.info("Platform %s", platform.platform())


@click.command()
@click.option('--width', '-w', default=1024, type=int, show_default=True,
              help="width in pixels for the image.")
@click.option('--height', '-h', default=768, type=int, show_default=True,
              help="height in pixels for the image.")
@click.option('--country', '-c', default='Germany', type=str, show_default=True,
              help="country as filter for the data")
def main(**options):
    """Visualizing covid19 data with matplotlib, panda and numpy."""
    initialize_logging()
    always = True
    url = "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv"
    logging.info("data url: %s", url)
    logging.info("image resolution: %(width)dx%(height)d pixel", options)
    logging.info("country filter: %(country)s", options)

    if not os.path.isfile("covid19.csv") or always:
        response = requests.get(url)
        with open('covid19.csv', 'wb') as stream:
            stream.write(response.content)

    df = pd.read_csv('covid19.csv')

    # searching for the country defined in the options
    country_filter = options['country'].lower()
    countries = set(country for country in df['countriesAndTerritories'])

    found = False
    for pos, country in enumerate(countries):
        if country.lower() == country_filter:
            country_filter = country
            found = True
            break

    if not found:
        logging.error("Country '%s' not found!", options['country'])
        sys.exit(1)

    # filter for concrete country
    df_concrete = df[df.countriesAndTerritories.eq(country_filter)]
    # sort by date ascending
    df_concrete = df_concrete.sort_values(by=['year', 'month', 'day'])
    df_concrete = df_concrete.reset_index(drop=True)

    fig, main_axes = plt.subplots(nrows=2, ncols=1, sharex=True)
    fig.suptitle(url, fontsize=8)

    # adjusting figure to show in requested resolution (default: 1024x768 pixel)
    DPI = fig.get_dpi()
    fig.set_size_inches(options['width']/float(DPI), options['height']/float(DPI))

    title = 'Corona Cases In %s (Total: %d)' % (country_filter, df_concrete['cases'].sum())
    axes = df_concrete.plot(x='dateRep', y='cases', title=title,
                            ax=main_axes[0],
                            kind='line', grid=True, color='#008000', legend=False)
    axes.set_xlabel('Date')
    axes.set_ylabel('Cases Per Day')

    # square polynomial fit for Corona cases
    x = np.arange(df_concrete['dateRep'].values.flatten().shape[0])
    p = np.poly1d(np.polyfit(x, df_concrete['cases'].values.flatten(), 4))
    main_axes[0].plot(x, p(x), linestyle='dashed', linewidth=0.75, color='#800000')

    title = 'Corona Deaths In %s (Total: %d)' % (country_filter, df_concrete['deaths'].sum())
    axes = df_concrete.plot(x='dateRep', y='deaths', title=title,
                            ax=main_axes[1],
                            kind='line', grid=True, color='#008000', legend=False)
    axes.set_xlabel('Date')
    axes.set_ylabel('Deaths Per Day')

    # square polynomial fit for Corona deaths
    p = np.poly1d(np.polyfit(x, df_concrete['deaths'].values.flatten(), 4))
    main_axes[1].plot(x, p(x), linestyle='dashed', linewidth=0.75, color='#800000')

    # export as png format
    plt.savefig('covid19.png', format='png')
    # show the window with the result
    plt.show()


if __name__ == "__main__":
    main()
