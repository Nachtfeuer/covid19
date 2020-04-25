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
from io import StringIO


class Application:
    """Application for visualizing Corona data."""

    DATA_URL = "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv"

    def __init__(self, options):
        """Initialize application with command line options."""
        self.options = options
        self.df = None
        self.df_concrete = None
        self.country_filter = self.options['country'].lower()
        self.first_day = None
        self.sum_of_cases = None
        self.sum_of_deaths = None

    @staticmethod
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

    def log_options(self):
        logging.info("data url: %s", Application.DATA_URL)
        logging.info("image resolution: %(width)dx%(height)d pixel", self.options)
        logging.info("country filter: %(country)s", self.options)
        logging.info("image format: %(format)s", self.options)
        logging.info("show viewer: %(viewer)s", self.options)
        logging.info("initial cases: %(initial_cases)d", self.options)
        logging.info("use cache: %(cache)s", self.options)
        logging.info("cache file: %(cache_file)s", self.options)

    def fetch_data(self):
        """Download Corona Data."""
        if self.options['cache']:
            if not os.path.isfile(self.options['cache_file']):
                logging.info("Downloading from %s", Application.DATA_URL)
                response = requests.get(Application.DATA_URL)
                with open(self.options['cache_file'], 'wb') as stream:
                    stream.write(response.content)

            self.df = pd.read_csv(self.options['cache_file'])
        else:
            logging.info("Downloading from %s", Application.DATA_URL)
            response = requests.get(Application.DATA_URL)
            self.df = pd.read_csv(StringIO(response.content.decode()))

    def provide_concrete_data(self):
        # searching for the country defined in the options
        if not self.country_filter == 'all':
            if not any(self.df.countriesAndTerritories.str.lower().eq(
                       self.country_filter).values.flatten()):
                logging.error("Country '%(country)s' not found!", self.options)
                sys.exit(1)

        if self.country_filter == 'all':
            # all countries ... we have to aggregate cases and deaths per day
            self.df_concrete = self.df.groupby('dateRep').agg({
                'cases': ['sum'], 'deaths': ['sum'],
                'year': ['min'], 'month': ['min'], 'day': ['min'], 'dateRep': ['min']
            })
            self.df_concrete.columns = ['cases', 'deaths', 'year', 'month', 'day', 'dateRep']
        else:
            # filter for concrete country
            self.df_concrete = self.df[
                self.df.countriesAndTerritories.str.lower().eq(self.country_filter)]

        # sort by date ascending
        self.df_concrete = self.df_concrete.sort_values(by=['year', 'month', 'day'])
        self.df_concrete = self.df_concrete.reset_index(drop=True)

        # allow to filter out rare cases at the beginning (default: take all)
        # that's for visualizing in the graphs only
        first_value_index = self.df_concrete.query(
            'cases >= %d' % self.options['initial_cases']).index[0]
        self.df_concrete = self.df_concrete.iloc[first_value_index:]

        # some information required for all graphs
        self.first_day = self.df_concrete['dateRep'].values.flatten()[0]
        self.sum_of_cases = self.df_concrete['cases'].sum()
        self.sum_of_deaths = self.df_concrete['deaths'].sum()

    def configure_subplots(self):
        """Define layout, main title and resolution of image."""
        fig, main_axes = plt.subplots(nrows=2, ncols=1, sharex=True)
        fig.suptitle(Application.DATA_URL, fontsize=8)

        # adjusting figure to show in requested resolution (default: 1024x768 pixel)
        DPI = fig.get_dpi()
        fig.set_size_inches(self.options['width']/float(DPI), self.options['height']/float(DPI))
        return fig, main_axes

    def plot(self, target, name, total):
        """Plotting concrete data and the relating trend line."""
        country = self.country_filter if not self.country_filter == 'all' else 'All Countries'
        title = 'Corona %s In %s (Total since %s: %d)' % \
            (name.title(), country.title(), self.first_day, total)
        self.df_concrete.plot(x='dateRep', y=name, title=title,
                              ax=target, kind='line',
                              grid=False, color='#008000', legend=False)

        # square polynomial fit for Corona cases
        x = np.arange(self.df_concrete['dateRep'].values.flatten().shape[0])
        p = np.poly1d(np.polyfit(x, self.df_concrete[name].values.flatten(), 4))
        target.plot(x, p(x), label='squares polynomial fit',
                    linestyle='dashed', linewidth=0.75, color='#800000')

        target.set_xlabel('Date')
        target.set_ylabel('%s Per Day' % name.title())
        target.tick_params(labelleft=True, labelright=True)
        target.grid(alpha=0.5)
        target.legend(loc='upper left')

    def visualize(self):
        """Plotting the data."""
        fig, main_axes = self.configure_subplots()

        self.plot(main_axes[0], 'cases', self.sum_of_cases)
        self.plot(main_axes[1], 'deaths', self.sum_of_deaths)

        # export by given format
        plt.savefig('covid19.%s' % self.options['format'], format=self.options['format'])

        if self.options['viewer']:
            # show the window with the result
            plt.show()

    def run(self):
        """Running the application logic."""
        Application.initialize_logging()
        self.log_options()
        self.fetch_data()
        self.provide_concrete_data()
        self.visualize()


@click.command()
@click.option('--width', '-w', default=1024, type=int, show_default=True,
              help="Width in pixels for the image.")
@click.option('--height', '-h', default=768, type=int, show_default=True,
              help="Height in pixels for the image.")
@click.option('--country', '-c', default='Germany',
              type=str, show_default=True, metavar="<NAME>",
              help="Country as filter for the data.")
@click.option('--format', '-f', default='png', type=click.Choice(['png', 'svg', 'jpg']),
              show_default=True,
              help="File format for image.")
@click.option('--viewer/--no-viewer', default=True, show_default=True,
              help="Show/hide the viewer.")
@click.option('--initial-cases', default=0, type=int, show_default=True,
              help="Ignoring intial cases less than than given value" +
                   " for visualization (totals are not affected)")
@click.option('--cache/--no-cache', default=False, show_default=True,
              help="Enable/Diable the cache.")
@click.option('--cache-file', default=os.path.join(os.getcwd(), 'covid19.csv'),
              type=str, show_default=True, metavar="<PATH>",
              help="Path and filename of the cache file.")
def main(**options):
    """Visualizing covid19 data with matplotlib, panda and numpy."""
    application = Application(options)
    application.run()


if __name__ == "__main__":
    main()
