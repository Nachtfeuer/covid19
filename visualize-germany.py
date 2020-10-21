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
import json
import requests
import click
import numpy as np
import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt


class Application:
    """Application for visualizing Corona data."""

    DATA_URL = 'https://opendata.arcgis.com/datasets/dd4580c810204019a7b8eb3e0b329dd6_0.geojson'

    def __init__(self, options):
        """Initialize application with command line options."""
        self.options = options

    @staticmethod
    def initialize_logging():
        """Initializing the logging (file and console)"""
        format = '%(asctime)s - %(levelname)s - %(message)s'
        # file based logging
        logging.basicConfig(filename='visualize-germany.log', level=logging.INFO, format=format)
        # adding console based logging
        consoleLogger = logging.StreamHandler()
        consoleLogger.setFormatter(logging.Formatter(format))
        logging.getLogger().addHandler(consoleLogger)
        # basic information at beginning (Python and platform)
        logging.info("Python %s", sys.version)
        logging.info("Platform %s", platform.platform())

    def log_options(self):
        """Logging of the options."""
        logging.info("use cache: %(cache)s", self.options)
        logging.info("cache file: %(cache_file)s", self.options)

    @staticmethod
    def create_df_from_json(content):
        data = {
            'date': [],
            'bundesland': [],
            'landkreis': [],
            'cases': [],
            'deaths': []
        }

        tree = json.loads(content)
        for entry in tree['features']:
            data['bundesland'].append(entry['properties']['Bundesland'])
            data['landkreis'].append(entry['properties']['Landkreis'])
            data['cases'].append(entry['properties']['AnzahlFall'])
            data['deaths'].append(entry['properties']['AnzahlTodesfall'])
            date = datetime.strptime(entry['properties']['Meldedatum'], "%Y/%m/%d %H:%M:%S")
            data['date'].append(date)

        return pd.DataFrame(data)

    def fetch_data(self):
        if self.options['cache']:
            if not os.path.isfile(self.options['cache_file']):
                logging.info("Downloading from %s", Application.DATA_URL)
                response = requests.get(Application.DATA_URL)
                with open(self.options['cache_file'], 'wb') as stream:
                    stream.write(response.content)

            with open(self.options['cache_file'], 'rb') as stream:
                self.df = Application.create_df_from_json(stream.read())
        else:
            logging.info("Downloading from %s", Application.DATA_URL)
            response = requests.get(Application.DATA_URL)
            self.df = Application.create_df_from_json(response.content.decode())

    def provide_concrete_data(self, final_filter):
        # searching for the country defined in the options
        if not final_filter == 'all':
            if not any(self.df[self.options['filter_by']].str.lower().eq(
                       final_filter).values.flatten()):
                logging.error("%s '%s' not found!", self.options['filter_by'].title(), final_filter)
                sys.exit(1)

        if final_filter == 'all':
            temp = self.df.groupby(['date']).agg({
                'date': ['min'],
                'bundesland': ['min'], 'landkreis': ['min'],
                'cases': ['sum'], 'deaths': ['sum']
            })
            temp.columns = ['date', 'bundesland', 'landkreis', 'cases', 'deaths']

            data = {
                'date': temp['date'].values.flatten(),
                'bundlesland': temp['bundesland'].values.flatten(),
                'landkreis': temp['landkreis'].values.flatten(),
                'cases': temp['cases'].values.flatten(),
                'deaths': temp['deaths'].values.flatten(),
            }
        else:
            temp = self.df.groupby(['date', self.options['filter_by']]).agg({
                'date': ['min'],
                'bundesland': ['min'], 'landkreis': ['min'],
                'cases': ['sum'], 'deaths': ['sum']
            })
            temp.columns = ['date', 'bundesland', 'landkreis', 'cases', 'deaths']

            data = {
                'date': temp['date'].values.flatten(),
                'bundesland': temp['bundesland'].values.flatten(),
                'landkreis': temp['landkreis'].values.flatten(),
                'cases': temp['cases'].values.flatten(),
                'deaths': temp['deaths'].values.flatten(),
            }

        df_concrete = pd.DataFrame(data)

        if not final_filter == 'all':
            # filter for concrete country
            df_concrete = df_concrete[
                df_concrete[self.options['filter_by']].str.lower().eq(final_filter)]

        # sort by date ascending
        df_concrete = df_concrete.sort_values(by=['date'])
        df_concrete = df_concrete.reset_index(drop=True)

        # some information required for all graphs
        first_day = df_concrete['date'].values.flatten()[0]
        sum_of_cases = df_concrete['cases'].sum()
        sum_of_deaths = df_concrete['deaths'].sum()

        # allow to filter out rare cases at the beginning (default: take all)
        # that's for visualizing in the graphs only
        first_value_index = df_concrete.query(
            'cases >= %d' % self.options['initial_cases']).index[0]
        df_concrete = df_concrete.iloc[first_value_index:]

        return df_concrete, first_day, sum_of_cases, sum_of_deaths

    def configure_subplots(self):
        """Define layout, main title and resolution of image."""
        fig, main_axes = plt.subplots(nrows=2, ncols=1, sharex=True)
        fig.suptitle(Application.DATA_URL, fontsize=8)

        # adjusting figure to show in requested resolution (default: 1024x768 pixel)
        DPI = fig.get_dpi()
        fig.set_size_inches(self.options['width'] / float(DPI), self.options['height'] / float(DPI))

        return fig, main_axes

    def plot(self, target, name, total, country_filter, df_concrete, first_day):
        """Plotting concrete data and the relating trend line."""
        first_day_str = np.datetime_as_string(first_day, unit='D')
        country = country_filter if not country_filter == 'all' else 'All Countries'
        title = 'Corona %s In %s (Total since %s: %d)' % \
            (name.title(), country.title(), first_day_str, total)

        # plot of the concrete data
        x = df_concrete['date'].values.flatten()
        target.plot(x, df_concrete[name].values.flatten(),
                    label=name, color='#008000')

        # square polynomial fit for Corona cases
        xt = np.arange(len(x))
        pt = np.poly1d(np.polyfit(xt, df_concrete[name].values.flatten(), 5))
        target.plot(x, pt(xt), label='squares polynomial fit',
                    linestyle='dashed', linewidth=0.75, color='#800000')

        target.set_title(title)
        target.set_xlabel('Date')
        target.set_ylabel('%s Per Day' % name.title())
        target.tick_params(labelleft=True, labelright=True)
        target.grid(alpha=0.5)
        target.legend(loc='upper left')

    def visualize(self, filter_value, data):
        """Plotting the data."""
        df_concrete, first_day, sum_of_cases, sum_of_deaths = data
        fig, main_axes = self.configure_subplots()

        # ensure that no negative axis is shown
        main_axes[0].set_ylim(0, df_concrete['cases'].max())
        main_axes[1].set_ylim(0, df_concrete['deaths'].max())

        self.plot(main_axes[0], 'cases', sum_of_cases, filter_value, df_concrete, first_day)
        self.plot(main_axes[1], 'deaths', sum_of_deaths, filter_value, df_concrete, first_day)

        # export by given format
        for format in self.options['format']:
            filename = 'covid19-germany-%s.%s' % (filter_value, format)
            filename = filename.replace(' ', '-')
            logging.info("Generating %s" % filename)
            plt.savefig(filename, format=format)

        return fig

    def run(self):
        """Running the application logic."""
        Application.initialize_logging()

        self.log_options()
        self.fetch_data()

        for filter_value in self.options['filter']:
            data = self.provide_concrete_data(filter_value.lower())
            self.visualize(filter_value.lower(), data)


@click.command()
@click.option('--cache/--no-cache', default=False, show_default=True,
              help="Enable/Diable the cache.")
@click.option('--cache-file', default=os.path.join(os.getcwd(), 'covid19-germany.json'),
              type=str, show_default=True, metavar="<PATH>",
              help="Path and filename of the cache file.")
@click.option('--filter-by', default='bundesland',
              type=click.Choice(['bundesland', 'landkreis']),
              show_default=True, metavar="<NAME>",
              help="value of the filter for the data")
@click.option('--filter', '-f', default=[''],
              type=str, show_default=True, metavar="<NAME>", multiple=True,
              help="value of the filter for the data (repeatable).")
@click.option('--initial-cases', default=0, type=int, show_default=True,
              help="Ignoring intial cases less than than given value" +  # noqa
                   " for visualization (totals are not affected)")
@click.option('--width', '-w', default=1024, type=int, show_default=True,
              help="Width in pixels for the image.")
@click.option('--height', '-h', default=768, type=int, show_default=True,
              help="Height in pixels for the image.")
@click.option('--format', '-f', default=['png'], type=click.Choice(['png', 'svg', 'jpg']),
              show_default=True, multiple=True,
              help="File format for image (repeatable).")
def main(**options):
    """Visualizing covid19 data with matplotlib, panda and numpy."""
    application = Application(options)
    application.run()


if __name__ == "__main__":
    main()
