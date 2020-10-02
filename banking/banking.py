import sqlite3
import random
from math import ceil


class BankCard:
    IIN = "400000"  # Issuer Identification Number (IIN)

    def __init__(self):
        self.user_card = ""
        self.user_pin = ""
        self.checksum = "0"
        self.balance = 0
        self.good_card = False

    def generate_card(self):
        can = str(random.randint(100000000, 999999999))  # Customer Account Number (CAN)
        self.luhn(BankCard.IIN + can + self.checksum, True)

    def generate_pin(self):
        pin = str(random.randint(0000, 9999))
        while len(pin) < 4:
            pin = "0" + pin
        self.user_pin = pin

    def luhn(self, card_num, create_new=False):
        num_arr = list(map(lambda x: int(x), card_num))
        chk_sum = num_arr[-1]
        del num_arr[-1]
        index = 1
        for n in num_arr:
            if index % 2 > 0:
                n = n * 2
                if n > 9:
                    n = n - 9
                    num_arr[index - 1] = n
                else:
                    num_arr[index - 1] = n
            index += 1
        aggregate = sum(num_arr)
        if (chk_sum + aggregate) % 10 == 0:
            self.user_card = card_num
            self.good_card = True
        elif create_new:
            self.checksum = str(ceil(aggregate / 10) * 10 - aggregate)
            self.user_card = card_num[:-1] + self.checksum
        else:
            self.good_card = False


class BankSys:
    def __init__(self, bank_card, database_nm='card.s3db'):
        self.logged_in = False
        self.card_acc = bank_card
        self.balance = bank_card.balance
        self.user = ""
        self.pin = ""
        self.transfer_card = ""
        self.d_conn = sqlite3.connect(database_nm)

        self.cursor = self.d_conn.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS card(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        pin TEXT NOT NULL,
        balance INTEGER DEFAULT 0
        );""")
        self.d_conn.commit()

    def lite_query(self, sql_query, item1, item2):
        data = (item1, item2)
        self.cursor.execute(sql_query, data)
        self.d_conn.commit()

    def add_new_account(self):
        self.card_acc.generate_card()
        self.card_acc.generate_pin()

        self.user = self.card_acc.user_card
        self.pin = self.card_acc.user_pin

        self.lite_query("""INSERT INTO card (number, pin) VALUES (?, ?);""", self.user, self.pin)

        print(f"\nYour card has been created\nYour card number:\n{self.user}")
        print(f"Your card PIN:\n{self.pin}\n")

    def add_income(self, income, transfer=False):
        sql_query = """UPDATE card SET balance = ? WHERE number = ?;"""

        if transfer:
            self.lite_query(sql_query, income, self.transfer_card)
            new_balance = self.balance - income
            self.lite_query(sql_query, new_balance, self.user)
        else:
            self.lite_query(sql_query, income, self.user)

    def do_add_income(self):
        income = int(input("\nEnter income:\n").strip())
        self.get_balance()
        self.balance += income
        self.add_income(self.balance)
        print("Income was added!\n")

    def test_card(self, card_num):
        sql_query = f"SELECT COUNT(number) FROM card WHERE number = {card_num};"
        self.cursor.execute(sql_query)
        res = self.cursor.fetchone()[0]

        self.card_acc.luhn(card_num)

        if not self.card_acc.good_card:
            print("Probably you made mistake in the card number. Please try again!\n")
            return False
        elif res == 0:
            print("Such a card does not exist.\n")
            return False
        else:
            self.transfer_card = card_num
            return True

    def transfer(self, amount):
        self.get_balance()

        if amount > self.balance:
            print("Not enough money!\n")
        else:
            self.add_income(amount, True)
            print("Success!\n")

    def do_transfer(self):
        print("\nTransfer")
        card_num = input("Enter card number:\n").strip()

        if self.test_card(card_num):
            amount = int(input("Enter how much you want to transfer:\n").strip())
            self.transfer(amount)

    def close_account(self):
        sql_query = """DELETE FROM card WHERE number = ? AND pin = ?;"""
        self.lite_query(sql_query, self.user, self.pin)
        print("\nThe account has been closed!\n")
        self.logged_in = False

    def get_balance(self):
        sql_query = """SELECT balance FROM card WHERE number = ? AND pin = ?;"""
        data = (self.user, self.pin)
        self.cursor.execute(sql_query, data)
        self.balance = self.cursor.fetchone()[0]
        return f"\nBalance: {self.balance}\n"

    def menu(self):
        s = f"1. Create an account\n2. Log into account\n0. Exit\n"

        if self.logged_in:
            s = f"1. Balance\n2. Add income\n3. Do transfer\n" \
                f"4. Close account\n5. Log out\n0. Exit\n"

        return int(input(s))

    def login(self):
        self.user = input("\nEnter your card number:\n").strip()
        self.pin = input("Enter your PIN:\n").strip()

        sql_query = """SELECT number FROM card WHERE number = ? AND pin = ?"""
        data = (self.user, self.pin)
        self.cursor.execute(sql_query, data)
        res = self.cursor.fetchone()

        if res is None:
            print("\nWrong card number or PIN!\n")
        else:
            print("\nYou have successfully logged in!\n")
            self.logged_in = True

    def leave(self):
        self.cursor.close()
        self.d_conn.close()
        print("\nBye!")

    def run(self):
        while True:
            option = self.menu()

            if self.logged_in:
                if option == 1:
                    print(self.get_balance())
                elif option == 2:
                    self.do_add_income()
                elif option == 3:
                    self.do_transfer()
                elif option == 4:
                    self.close_account()
                elif option == 5:
                    self.logged_in = False
                    print("\nYou have successfully logged out!\n")
                elif option == 0:
                    self.leave()
                    break
            else:
                if option == 1:
                    self.add_new_account()
                elif option == 2:
                    self.login()
                elif option == 0:
                    self.leave()
                    break


bankcard = BankCard()
app = BankSys(bankcard)
app.run()