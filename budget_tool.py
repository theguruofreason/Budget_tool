#!/usr/bin/python3

import sys
from enum import Enum
import os
import re
import csv


class InPay(Enum):
    unknown = 'unknown'
    income = 'income'
    payment = 'payment'


class TransactionClass(Enum):
    income = 'income'
    rent = 'rent'
    utilities = 'utilities'
    groceries = 'groceries'
    transportation = 'transportation'
    dining = 'dining'
    entertainment = 'entertainment'
    subscriptions = 'subscriptions'
    miscellaneous = 'miscellaneous'


class Transaction(object):
    def __init__(self, row):
        self.row = row
        self.date_regex = re.compile(r"^\d\d/\d\d/\d\d\d\d")
        self.amount_regex = re.compile(r"-?\d*.\d*")
        self.in_out = InPay.unknown
        for column in row:
            if self.date_regex.match(column):
                self.month, self.day, self.year = column.split('/')
            elif self.amount_regex.match(column):
                self.amount = self.parse_amount(column)
            # not the best way to determine a description column...
            elif len(column) < 1:
                self.description = column
        self.amount = self.parse_amount(self.row)
        self.transaction_class = TransactionClass

    def parse_amount(self, amount):
        if amount[0] == '-':
            self.in_out = InPay.payment
            amount = amount[1:]
        else:
            self.in_out = InPay.income

        return float(amount)


class BudgetTool(object):
    def __init__(self, inputs, outdir = '', **kwargs):
        self.inputs = inputs
        self.outdir = outdir
        self.transaction_classes = {TransactionClass.income: [],
                                    TransactionClass.rent: [],
                                    TransactionClass.utilities: [],
                                    TransactionClass.groceries: [],
                                    TransactionClass.transportation: [],
                                    TransactionClass.dining: [],
                                    TransactionClass.entertainment: [],
                                    TransactionClass.subscriptions: [],
                                    TransactionClass.miscellaneous: []}

    def parse_csv_file(self, file):
        try:
            with open(file, 'r', newline='') as f:
                csv_reader = csv.reader(f)
        except Exception as e:
            print("failed to read file: {}".format(file))
            print("error: {}".format(e))
            print("continuing...")
        for row in csv_reader:
            # remove blank columns
            row = filter(None, row)
            transaction = Transaction(row)

    def read_inputs(self):
        for path in self.inputs:
            if os.path.isdir(path):
                _, _, filenames = os.walk(path)
                for file in filenames:
                    self.parse_csv_file(file)
            elif os.path.isfile(path):
                self.parse_csv_file(path)




def app():


if __name__ == '__main__':
    sys.exit(app())