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
import numpy as np
import pandas as pd
from io import StringIO

import matplotlib
import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import ttk


class Application:
    """Application for visualizing Corona data."""

    DATA_URL = "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv"

    def __init__(self, options):
        """Initialize application with command line options."""
        self.options = options
        self.df = None
        self.figures = []
        self.root = None
        self.notebook = None
        self.page_class = None

        if self.options['viewer']:
            matplotlib.use("TkAgg")
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            class Page(tk.Frame):
                """Each page displays one country."""

                def __init__(self, parent, figure):
                    """Initialize page."""
                    super(Page, self).__init__(parent)
                    self.figure_canvas_agg = FigureCanvasTkAgg(figure, master=self)
                    self.figure_canvas_agg.get_tk_widget().pack(fill=tk.BOTH, expand=tk.YES)
                    self.figure_canvas_agg.draw()

            self.page_class = Page

            self.root = tk.Tk()
            self.root.title("Corona Data Visualization")
            self.root.geometry('1024x768+50+50')
            self.root.attributes('-alpha', self.options['transparency'])
            self.root.protocol("WM_DELETE_WINDOW", self.on_destroy)
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=tk.YES)

    def on_destroy(self):
        """Closing the application but before closing the figures."""
        for figure in self.figures:
            plt.close(figure)
        self.root.destroy()

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
        """Logging of the options."""
        logging.info("data url: %s", Application.DATA_URL)
        logging.info("image resolution: %(width)dx%(height)d pixel", self.options)
        logging.info("country filter: %(country)s", self.options)
        logging.info("image format: %(format)s", self.options)
        logging.info("show viewer: %(viewer)s", self.options)
        logging.info("initial cases: %(initial_cases)d", self.options)
        logging.info("use cache: %(cache)s", self.options)
        logging.info("cache file: %(cache_file)s", self.options)
        logging.info("transparency: %(transparency)g", self.options)

    def fetch_data(self):
        """Download Corona Data (or use the cache)."""
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

    def provide_concrete_data(self, country_filter):
        # searching for the country defined in the options
        if not country_filter == 'all':
            if not any(self.df.countriesAndTerritories.str.lower().eq(
                       country_filter).values.flatten()):
                logging.error("Country '%s' not found!", country_filter)
                sys.exit(1)

        if country_filter == 'all':
            temp = self.df.groupby('dateRep').agg({
                'cases': ['sum'], 'deaths': ['sum'], 'dateRep': ['min'],
                'countriesAndTerritories': ['min']
            })
            temp.columns = ['cases', 'deaths', 'dateRep', 'countriesAndTerritories']

            data = {
                'date': [pd.to_datetime(entry, format="%d/%m/%Y") for entry in temp['dateRep']],
                'cases': temp['cases'].values.flatten(),
                'deaths': temp['deaths'].values.flatten(),
                'countriesAndTerritories': temp['countriesAndTerritories'].values.flatten()
            }
        else:
            data = {
                'date': [pd.to_datetime(entry, format="%d/%m/%Y") for entry in self.df['dateRep']],
                'cases': self.df['cases'].values.flatten(),
                'deaths': self.df['deaths'].values.flatten(),
                'countriesAndTerritories': self.df['countriesAndTerritories'].values.flatten()
            }

        df_concrete = pd.DataFrame(data)

        if not country_filter == 'all':
            # filter for concrete country
            df_concrete = df_concrete[
                df_concrete.countriesAndTerritories.str.lower().eq(country_filter)]

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

    def visualize(self, country_filter, data):
        """Plotting the data."""
        df_concrete, first_day, sum_of_cases, sum_of_deaths = data
        fig, main_axes = self.configure_subplots()

        # ensure that no negative axis is shown
        main_axes[0].set_ylim(0, df_concrete['cases'].max())
        main_axes[1].set_ylim(0, df_concrete['deaths'].max())

        self.plot(main_axes[0], 'cases', sum_of_cases, country_filter, df_concrete, first_day)
        self.plot(main_axes[1], 'deaths', sum_of_deaths, country_filter, df_concrete, first_day)

        # export by given format
        for format in self.options['format']:
            filename = 'covid19-%s.%s' % (country_filter, format)
            logging.info("Generating %s" % filename)
            plt.savefig(filename, format=format)

        return fig

    def add_page(self, country, figure):
        """Adding one page to the notebook."""
        page = self.page_class(self.notebook, figure)
        page.pack(fill=tk.BOTH, expand=tk.YES)
        self.notebook.add(page, text=country.title())

    def run(self):
        """Running the application logic."""
        Application.initialize_logging()

        self.log_options()
        self.fetch_data()

        for country in self.options['country']:
            data = self.provide_concrete_data(country.lower())
            figure = self.visualize(country.lower(), data)

            if self.options['viewer']:
                self.figures.append(figure)
                self.add_page(country.title(), figure)

        if self.options['viewer']:
            # event loop (keeps application running)
            self.root.mainloop()


@click.command()
@click.option('--width', '-w', default=1024, type=int, show_default=True,
              help="Width in pixels for the image.")
@click.option('--height', '-h', default=768, type=int, show_default=True,
              help="Height in pixels for the image.")
@click.option('--country', '-c', default=['Germany'],
              type=str, show_default=True, metavar="<NAME>", multiple=True,
              help="Country as filter for the data (repeatable).")
@click.option('--format', '-f', default=['png'], type=click.Choice(['png', 'svg', 'jpg']),
              show_default=True, multiple=True,
              help="File format for image (repeatable).")
@click.option('--viewer/--no-viewer', default=True, show_default=True,
              help="Show/hide the viewer.")
@click.option('--initial-cases', default=0, type=int, show_default=True,
              help="Ignoring intial cases less than than given value" +  # noqa
                   " for visualization (totals are not affected)")
@click.option('--cache/--no-cache', default=False, show_default=True,
              help="Enable/Diable the cache.")
@click.option('--cache-file', default=os.path.join(os.getcwd(), 'covid19.csv'),
              type=str, show_default=True, metavar="<PATH>",
              help="Path and filename of the cache file.")
@click.option('--transparency', '-a', default=0.8, type=click.FloatRange(0.5, 1.0),
              show_default=True, help="Enables transparency for viewer")
def main(**options):
    """Visualizing covid19 data with matplotlib, panda and numpy."""
    application = Application(options)
    application.run()


if __name__ == "__main__":
    main()
