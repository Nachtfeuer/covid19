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
 - the **sharex** is the way to organize that the X labels are appear at
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
