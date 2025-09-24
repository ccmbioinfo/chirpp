import pandas as pd


def get_probs(database, start_date, complaint_filter):
    """
    Get the minimum probability of a visit based on chief complaints and start date. This is there because daily run cutoffs
    are not reliable due to random fluctations, but at 30 days things get quite stable
    :param database: chirpp.database.DataBase instance
    :param start_date: start date to be queries
    :param complaint_filter: see config.yaml, these are complaints that are to be 100% chirpp cases based on chief complaints
    :return: return the min prob cutoff
    """
    probs = pd.read_sql(
        f"select min(probs) from visits where chief_complaint in {','.join(complaint_filter)} and arrival_date >= '{start_date}'",
        con=database.engine)

    return probs[0]