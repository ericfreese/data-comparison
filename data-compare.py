import argparse
from itertools import chain

import duckdb
from sqlalchemy import and_, column, func, select, text, true


def _read_csv(group_cols, measures):
    def _read_csv(file):
        types = {c: "VARCHAR" for c in group_cols} | {c: "NUMERIC" for c in measures}
        return text(f"read_csv('{file}', header = true, types = {types})")

    return _read_csv


def compare(before_file, after_file, group_cols, measures, filters):
    read_csv = _read_csv(group_cols, measures)

    query = select(
        *[column(gc) for gc in group_cols],
        *[func.sum(column(c)).label(c) for c in measures],
    ).group_by(*[column(gc) for gc in group_cols])

    before = query.select_from(read_csv(before_file))
    after = query.select_from(read_csv(after_file))

    b = before.subquery().alias("b")
    a = after.subquery().alias("a")

    join_cond = true()
    for gc in group_cols:
        join_cond = and_(join_cond, b.c[gc].isnot_distinct_from(a.c[gc]))

    joined = (
        select(
            *[func.coalesce(b.c[gc], a.c[gc]).label(gc) for gc in group_cols],
            *chain.from_iterable(
                [
                    b.c[m].label(f"b_{m}"),
                    a.c[m].label(f"a_{m}"),
                    (func.coalesce(a.c[m], 0) - func.coalesce(b.c[m], 0)).label(
                        f"d_{m}"
                    ),
                ]
                for m in measures
            ),
        )
        .join_from(a, b, join_cond, full=True)
        .order_by(*[func.coalesce(b.c[gc], a.c[gc]) for gc in group_cols])
    )

    j = joined.subquery().alias("j")
    filtered = select(j).where(*[j.c[c] == v for c, v in filters.items()])
    query_str = filtered.compile(compile_kwargs={"literal_binds": True}).string

    return duckdb.sql(query_str)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "before_file",
        metavar="before",
        type=str,
        help="file to start with",
    )

    parser.add_argument(
        "after_file",
        metavar="after",
        type=str,
        help="file to compare against",
    )

    parser.add_argument(
        "-m",
        "--measures",
        metavar="col",
        type=str,
        nargs="+",
        help="columns to sum and compare",
        required=True,
    )

    parser.add_argument(
        "-g",
        "--group-cols",
        metavar="col",
        type=str,
        nargs="+",
        help="columns to group and join by",
        required=True,
    )

    return parser.parse_args()


def parse_group_cols(group_cols_with_filters):
    filters = {}
    group_cols = []

    for gcwf in group_cols_with_filters:
        if len(parts := gcwf.split("=", maxsplit=1)) == 2:
            group_cols.append(parts[0])
            filters[parts[0]] = parts[1]
        else:
            group_cols.append(gcwf)

    return (group_cols, filters)


args = parse_args()

group_cols, filters = parse_group_cols(args.group_cols)

output = compare(
    args.before_file,
    args.after_file,
    group_cols,
    args.measures,
    filters,
)

output.write_csv("/dev/stdout")
