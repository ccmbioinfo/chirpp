import pandas as pd



def scramble_mrn(mrn):
    """
    takes the mrn value of the note and runs a simple scramble
    :param mrn: mrn
    :return: scrambled mrn
    """
    mrn = str(mrn).strip()
    last_digit = (int(mrn[-1]) + int(mrn[-2])) % 10
    return mrn[:-2] + mrn[-1] + mrn[-2] + str(last_digit)



# right now I'm not changing the column names, I'm relying on the existing reports and they will remain constant and
# the column names will not be changed for no good reason

def prepare_report(visits, cases, patients, problems):
    """
    this prepares the report from the database, not to be confused with the postprocess methods, when you want to generate
    a report from the db for a given date range (see above) you will use this method
    :param visits:
    :param cases:
    :param patients:
    :param problems:
    :return:
    """
    pass
    #TODO

