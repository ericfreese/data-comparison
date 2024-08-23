# Data Comparison Tool

Takes two CSV files with overlapping column names and generates a comparison report (printed to stdout in CSV format) by grouping the data in each file by specified qualitative columns, aggregating (summing) specified quantitative columns, joining the aggregated data together on the grouped columns, and reporting before/after values of the quantitative aggregates.

## Example

`before.csv`:

```csv
name,color,amount
foo,red,3
foo,green,2
foo,blue,4
bar,red,5
bar,green,3
```

`after.csv`:

```csv
name,color,amount
foo,red,5
foo,green,2
bar,red,5
bar,green,2
bar,blue,4
```

```sh
$ data-compare before.csv after.csv -m amount -g color
color,b_amount,a_amount,d_amount
blue,4.000,4.000,0.000
green,5.000,4.000,-1.000
red,8.000,10.000,2.000
```

```sh
$ data-compare before.csv after.csv -m amount -g name
name,b_amount,a_amount,d_amount
bar,8.000,11.000,3.000
foo,9.000,7.000,-2.000
```

```sh
$ data-compare before.csv after.csv -m amount -g color name
color,name,b_amount,a_amount,d_amount
blue,bar,,4.000,4.000
blue,foo,4.000,,-4.000
green,bar,3.000,2.000,-1.000
green,foo,2.000,2.000,0.000
red,bar,5.000,5.000,0.000
red,foo,3.000,5.000,2.000
```

## Usage

```
usage: data-compare [-h] -m col [col ...] -g col [col ...] before after

positional arguments:
  before                file to start with
  after                 file to compare against

options:
  -h, --help            show this help message and exit
  -m col [col ...], --measures col [col ...]
                        columns to sum and compare
  -g col [col ...], --group-cols col [col ...]
                        columns to group and join by
```

Filters can be applied to a grouped column by suffixing it with `=<value>` so using `-g foo=bar` would group by the `foo` column and filter rows to only those where `foo` is equal to `bar`

## Initializing virtual env for dev

```sh
pipenv sync --dev
```

## Run in dev environment

```sh
pipenv run python data-compare.py
```

## Build standalone executable

```sh
pipenv run pyinstaller data-compare.spec
```
