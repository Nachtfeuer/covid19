# Welcome to the Python based visualization for covid19 data

## Purpose

Also I have used the RSS Feed from RKI I always have been
seeing the snasphot of the day only and I were interested
to the see the development from the past weeks and months
until now.

The final result looks like this:

![](docs/images/covid19.png)

## Quickstart

The whole thing is written in Python. You require to have some
libraries installed:

```
pip install requests numpy pandas matplotlib
```

With this you simply can run the script:

```
python visualize.py
```

Running this script a file covid19.csv is generated and
a file covid19.png is generated. In addition the viewer
is started showing you the results:

![](docs/images/viewer.png)

## Links

 - https://opendata.ecdc.europa.eu/covid19/casedistribution/csv
