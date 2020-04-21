# Welcome to Pandas and Friends

## Libraries

Those libraries **pandas**, **numpy** and **matplotlib**
are playing the game together. This document explains a bit
of what have been done in the small script *visualize.py*
you can find in this repository.

## Download the CSV data into a dataframe

An also well known library is **requests** with it you
can download a file or query a response from a given
endpoint. The following code provides you the covid19 data
in a dataframe:

```python
url = "https://opendata.ecdc.europa.eu/covid19/casedistribution/csv"

response = requests.get(url)
with open('covid19.csv', 'wb') as stream:
    stream.write(response.content)

df = pd.read_csv('covid19.csv')
```

## Filtering and sorting

Of course - since I'm mainly interested in my own country -
I wrote it like that:

```python
df_concrete = df[df.countriesAndTerritories.eq('Germany')]
# sort by date ascending
df_concrete = df_concrete.sort_values(by=['year', 'month', 'day'])
df_concrete = df_concrete.reset_index(drop=True)
```

The CSV contains those three columns and you can define it as shown
to sort the columns in the defined order: first by year, secondly by month
and third by day.

## Adjusting multiple plots in two graphs

The way to get multiple plots into one output is to use **subplots**.
The **figure** is the overall container and the **main_axes** represent
the target where to plot. In this example we have to rows and one column.

Some notes:
 - the **sharex** is the way to organize that the X labels are appearing at
   the bottom plot only since we have a vertical layout it make sense.
 - The method **suptitle** is a title for the container while also each
   subplot can have its own title (as done).
 - The DPI is used to calculate and set the dimension of the figure in
   pixels. Here it is defined to have 1024x768 pixels.

```python
fig, main_axes = plt.subplots(nrows=2, ncols=1, sharex=True)
fig.suptitle(url, fontsize=8)

# adjusting figure to show in resolution of 1024x768 pixel
DPI = fig.get_dpi()
fig.set_size_inches(1024/float(DPI), 768/float(DPI))
```

## Plotting a dataframe

I'm explaining that for **case** only since it is pretty the same for
the other plot. Some notes:

 - Since the CSV data are data for each day I've been looking forward
   to have the overall sum in the title. The **sum** function can be
   used very easily on a column of a dataframe as seen here.
 - The parameters **x** and **y** are simply the names of the columns
   in the dataframe to be used for the plot.
 - The **ax** is the way to define which plot target (layout) to use;
   in given example the plot is placed in the upper row.
 - Since I'm printing just one series I don't need a legend (**legend=False**)
 - All other parameters should be understandable.
 - A plot gives access to the axes and can be used to adjust labels for X and Y.

```python
title = 'Corona Infizierte in Deutschland (Insgesamt: %d)' % df_concrete['cases'].sum()
axes = df_concrete.plot(x='dateRep', y='cases', title=title,
                       ax=main_axes[0],
                       kind='line', grid=True, color='#008000', legend=False)
axes.set_xlabel('Datum')
axes.set_ylabel('Infizierte pro Tag')
```

## Trend line

Of course I also would like to have a trend line. Also it is quite easy to use
I don't feel too comfortable with; here the hints:

 - The **polyfit** cannot work with the date string but that's not important
   since we create a trendline for the Y values only. So mainly I create an
   array with a range of values (example: if there would be 3 values it would be [0, 1, 2])
   When I find a better code I will modify here...
 - The second code line is create the regression function
 - The last line plots onto the upper row using **x=x** and **y=p(x)** as values.
 - The other parameters should be understandable.

```python
# square polynomial fit for Corona cases
x = np.arange(df_concrete['dateRep'].values.flatten().shape[0])
p = np.poly1d(np.polyfit(x, df_concrete['cases'].values.flatten(), 4))
main_axes[0].plot(x, p(x), linestyle='dashed', linewidth=0.75, color='#800000')
```

## Final

The one line generates the PNG file (just exchange "png" with "svg" works fine).
The last line is displaying the matplotlib viewer; running such script
automated you also could comment it.

```
# export as png format
plt.savefig('covid19.png', format='png')
# show the window with the result
plt.show()
```

## Links

 - https://requests.readthedocs.io/en/master/
 - https://click.palletsprojects.com/en/7.x/
