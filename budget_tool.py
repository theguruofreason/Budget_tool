#!/usr/bin/python3

import sys
from enum import Enum
import os
import re
import csv
import argparse
import json


class InPay(Enum):
    unknown = 'unknown'
    income = 'income'
    payment = 'payment'


class TransactionClass(Enum):
    income = 'income'
    rent = 'rent'
    utilities = 'utilities'
    insurance = 'insurance'
    credit_card_payment = 'credit_card_payment'
    groceries = 'groceries'
    transportation = 'transportation'
    dining = 'dining'
    entertainment = 'entertainment'
    subscriptions = 'subscriptions'
    miscellaneous = 'miscellaneous'

rent_keywords = ['lagoons', 'Atwater']
utilities_keywords = ['PG&E']
insurance_keywords = ['']
credit_card_payment_keywords = ['PLATINUM', 'CARD', 'TRANSFER']
groceries_keywords = ['SAFEWAY', 'STORE', 'LUCKY', 'TRADER', 'JOE\'S', 'WHOLEFDS']
transportation_keywords = ['ARCO', 'CHEVRON', 'SHELL', 'Station']
dining_keywords = ['KENTA', 'RAMEN', 'CHIPTOLE', 'ETHEIOPIAN', 'CROUCHING',
                   'TIGER', 'GRUBHUB', 'CORNER', 'BAKERY', 'AKIZU', 'SUSHI',
                   'BAR']
entertainment_keywords = ['Video', 'On De', 'STEAM', 'GAMES', 'PANDORA', 'GOG',
                          'NICOSA', 'AMC', 'CINEMARK', 'MOVIE']
subscriptions_keywords = ['RECURRING', 'SAM HARRIS', 'AmazonPrime', 'Member']


class Transaction(object):
    def __init__(self, row, sensitivity = 1):
        self.row = row
        self.sensitivity = sensitivity
        self.processing_date_regex = re.compile(r"^\d\d/\d\d/\d\d\d\d")
        self.authorization_date_regex = re.compile(r"\s\d/\d\s")
        self.amount_regex = re.compile(r"-?\d*.\d*")
        self.in_out = InPay.unknown
        for column in row:
            if self.processing_date_regex.match(column):
                self.processing_month, self.processing_day, self.processing_year = column.split('/')
            elif self.amount_regex.match(column):
                self.amount = self.parse_amount(column)
            # not the best way to determine a description column...
            elif len(column) > 1:
                self.description = column
        try:
            self.authorization_month, self.authorization_day = (
                self.authorization_date_regex.match(self.description).match.split('/').zip())
        except:
            self.authorization_month = None
            self.authorization_day = None
        self.amount = self.parse_amount(self.row)
        self.keyword_classes = {TransactionClass.rent: rent_keywords,
                                TransactionClass.utilities: utilities_keywords,
                                TransactionClass.insurance: insurance_keywords,
                                TransactionClass.credit_card_payment: credit_card_payment_keywords,
                                TransactionClass.groceries: groceries_keywords,
                                TransactionClass.transportation: dining_keywords,
                                TransactionClass.entertainment: entertainment_keywords,
                                TransactionClass.subscriptions: subscriptions_keywords}
        self.transaction_classes = []
        self.determine_transaction_classes()

    def parse_amount(self, amount):
        if amount[0] == '-':
            self.in_out = InPay.payment
            amount = amount[1:]
        else:
            self.in_out = InPay.income

        return float(amount)

    def determine_transaction_class(self):
        class_hits = {key: value for (key, value) in (
            zip([*self.keyword_classes], [0]*len([*self.keyword_classes])))}
        for transaction_class, keywords in self.keyword_classes.items():
            for keyword in keywords:
                if keyword.lower() in self.description.lower():
                    class_hits[transaction_class] += 1
            if class_hits[transaction_class] >= self.sensitivity:
                self.transaction_classes.append(transaction_class)

        if not self.transaction_classes:
            self.transaction_classes.append(TransactionClass.miscellaneous)


class BudgetTool(object):
    def __init__(self, inputs = '', load_budget_uri = '', output_uri = '', sensitivity = 1, **kwargs):
        self.inputs = inputs
        self.load_budget_uri = load_budget_uri
        self.output_uri = output_uri
        self.sensitivity = sensitivity
        self.transaction_classes = {TransactionClass.income: [],
                                    TransactionClass.rent: [],
                                    TransactionClass.utilities: [],
                                    TransactionClass.insurance: [],
                                    TransactionClass.groceries: [],
                                    TransactionClass.credit_card_payment: [],
                                    TransactionClass.transportation: [],
                                    TransactionClass.dining: [],
                                    TransactionClass.entertainment: [],
                                    TransactionClass.subscriptions: [],
                                    TransactionClass.miscellaneous: []}
        self.all_transactions = []
        if load_budget_uri:
            self.load_budget(load_budget_uri)

    def transaction_captured(self, transaction):
        return transaction in self.all_transactions

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
            try:
                transaction = Transaction(row, self.sensitivity)
            except Exception as e:
                print(e)
                print("Failed to parse transaction: {}".format(row))
            if self.transaction_captured(transaction):
                continue
            for transaction_class in transaction.transaction_classes:
                self.transaction_classes[transaction_class].append(transaction)

    def read_inputs(self):
        for path in self.inputs:
            if os.path.isdir(path):
                _, _, filenames = os.walk(path)
                for file in filenames:
                    self.parse_csv_file(file)
            elif os.path.isfile(path):
                self.parse_csv_file(path)

    def save_json(self):
        with open(self.output_uri, 'w') as output_file:
            json.dump(self, output_file)

    def handle_user_input(self):
        input_parser = argparse.ArgumentParser()
        prompt = "What would you like to do?\n"
        prompt += "\'vt\' - View transactions"
        input("")

def app():
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs',
                        nargs='+',
                        help="A list of csv files or directories to be searched for csv " +
                              "files which are bank transaction logs. Currently, only Wells Fargo " +
                              "transaction logs are supported.")
    parser.add_argument('-l', '--load',
                        dest='load_uri',
                        help="A budget tool .json file to load. All transactions from input files " +
                             "will be combined with transactions found in the loaded .json.")
    parser.add_argument('-o', '--output',
                        dest='output_uri',
                        help="The exact file location to save the output .json file representing " +
                             "the transaction log. If none is provided, output will not be saved.")
    parser.add_argument('-s', '--sensitivity',
                        dest='sensitivity',
                        help="Option to set sensitivity for categorizing transactions. " +
                             "It represents the number of matching keywords for classification")
    args = parser.parse_args()
    inputs, load_uri, output_uri, sensitivity = args.inputs, args.load_uri, args.output_uri, args.sensitivity

    if load_uri:
        with open(load_uri, 'r') as load_file:
            budget_tool = json.load(load_file)
            if inputs:
                budget_tool.inputs = inputs
            if output_uri:
                budget_tool.output_uri = output_uri
            if sensitivity:
                budget_tool.sensitivity = sensitivity
    else:
        budget_tool = BudgetTool(inputs=inputs, output_uri=output_uri, sensitivity=sensitivity)

    budget_tool.save_json()



if __name__ == '__main__':
    sys.exit(app())