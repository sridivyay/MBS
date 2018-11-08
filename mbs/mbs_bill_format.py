from datetime import datetime
import matplotlib.pyplot as plt

import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


def get_bill_data(db_result):
    columns = ['Item', 'Quantity', 'Cost', 'Purchase Date']
    df = pd.DataFrame(columns=columns)
    total_cost = 0
    for record in db_result:
        purchase_time = datetime.strptime(str(record['purchase_time']), '%Y-%m-%d %H:%M:%S')
        purchase_time = str(purchase_time.day) + '-' + str(purchase_time.month) + '-' + str(purchase_time.year)
        item_name = str(record['Item_name'])
        cost = str(int(record['cost']))
        quantity = str(record['qty'])
        data = [item_name, quantity, cost, purchase_time]
        total_cost = total_cost + int(record['cost'])
        df.loc[len(df)] = data
    data = ['Total Cost', '', total_cost, '']
    df.loc[len(df)] = data
    return df


def generate_bill_pdf(df, user_id):
    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')
    left, width = .25, .5
    bottom, height = .25, .5
    top = bottom + height

    ax.text(left, top, 'Bill Generated for the user: ' + str(user_id),
            horizontalalignment='left',
            verticalalignment='top',
            transform=ax.transAxes)

    ax.table(cellText=df.values, colLabels=df.columns, loc='center')
    fig.tight_layout()
    pp = PdfPages(str(user_id) + '.pdf')
    pp.savefig()
    pp.close()
