import numbers
import datetime
from collections import namedtuple

Confirmation = namedtuple('Confirmation', 'account_number, transaction_code, transaction_id, time_utc, time')


class Timezone:

    def __init__(self, name, offset_hours, offset_minutes):
        if name is None or len(str(name).strip()) == 0:
            raise ValueError('Timezone name can not be none')
        self._name = str(name).strip()

        if not isinstance(offset_hours, numbers.Integral):
            raise ValueError('Offset hours is not integer')

        if not isinstance(offset_minutes, numbers.Integral):
            raise ValueError('Offset minutes is not integer')

        if not -59 < int(offset_minutes) < 59:
            raise ValueError('offset minutes out of range')

        offset = datetime.timedelta(hours=int(offset_hours), minutes=int(offset_minutes))
        if offset < datetime.timedelta(-12, 00) or offset > datetime.timedelta(14, 00):
            raise ValueError('offset out of range')

        self._offset_hour = offset_hours
        self._offset_minutes = offset_minutes
        self._offset = offset

    @property
    def offset(self):
        return self._offset

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        if not isinstance(other, Timezone):
            return False
        if self._name == other._name and self._offset == other._offset:
            return True
        else:
            return False

    def __repr__(self):
        return f"Timezone(name='{self._name}')\n" \
               f"offset = {self.offset}"


class Transaction:
    def __init__(self, start_id):
        self.start_id = start_id

    def next(self):
        self.start_id += 1
        return self.start_id


def make_transaction():
    new_transaction_id = Account.transaction_counter.next()


class Account:
    _interest_rate = 0.5
    transaction_counter = Transaction(99)

    _transaction_codes = {
        'deposit': 'D',
        'withdraw': 'W',
        'interest': 'I',
        'rejected': 'X'
    }

    def __init__(self, account_no, first_name, last_name, initial_balance=0, timezone=None):
        self._first_name = None
        self._last_name = None
        self._account_number = account_no
        self.first_name = first_name
        self.last_name = last_name
        if timezone is None:
            timezone = Timezone('UTC', 0, 0)
        self.timezone = timezone

        self._balance = float(initial_balance)

    @property
    def account_number(self):
        return self._account_number

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self.validate_and_set_name('_first_name', value, 'First Name')

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self.validate_and_set_name('_last_name', value, 'Last Name')

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    @property
    def balance(self):
        return self._balance

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, value):
        if not isinstance(value, Timezone):
            raise ValueError('Time zone must be a valid TimeZone object.')
        self._timezone = value

    @classmethod
    def get_interest_rate(cls):
        return cls._interest_rate

    @classmethod
    def set_interest_rate(cls, value):
        if not isinstance(value, numbers.Real):
            raise ValueError('Interest rate must be a real number')
        if value < 0:
            raise ValueError('Interest rate cannot be negative.')
        cls._interest_rate = value

    def validate_and_set_name(self, property_name, value, field_title):
        if value is None or len(str(value).strip()) == 0:
            raise ValueError(f'{field_title} cannot be empty.')
        setattr(self, property_name, value)

    def generate_confirmation_code(self, transaction_code):
        dt_str = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f'{transaction_code}-{self.account_number}-{dt_str}-{Account.transaction_counter.next()}'

    @staticmethod
    def parse_confirmation_code(confirmation_code, preferred_time_zone=None):
        parts = confirmation_code.split('-')
        if len(parts) != 4:
            raise ValueError('Invalid confirmation code')

        transaction_code, account_number, raw_dt_utc, transaction_id = parts

        try:
            dt_utc = datetime.datetime.strptime(raw_dt_utc, '%Y%m%d%H%M%S')
        except ValueError as ex:
            raise ValueError('Invalid transaction datetime') from ex

        if preferred_time_zone is None:
            preferred_time_zone = Timezone('UTC', 0, 0)

        if not isinstance(preferred_time_zone, Timezone):
            raise ValueError('Invalid TimeZone specified.')

        dt_preferred = dt_utc + preferred_time_zone.offset
        dt_preferred_str = f"{dt_preferred.strftime('%Y-%m-%d %H:%M:%S')} ({preferred_time_zone.name})"

        return Confirmation(account_number, transaction_code, transaction_id, dt_utc.isoformat(), dt_preferred_str)

    @staticmethod
    def validate_real_number(value, min_value = None):
        if not isinstance(value, numbers.Real):
            raise ValueError("Value must be real")
        if value<min_value:
            raise ValueError(f"value is less than {min_value}")
        return value

    def deposit(self, value):
        value = Account.validate_real_number(value, min_value=0.01)

        transaction_code = Account._transaction_codes['deposit']

        conf_code = self.generate_confirmation_code(transaction_code)

        self._balance += float(value)
        return conf_code

    def withdraw(self, value):
        value = Account.validate_real_number(value, min_value=0.01)
        accepted = False
        if self.balance - value < 0:
            transaction_code = Account._transaction_codes['rejected']
        else:
            transaction_code = Account._transaction_codes['withdraw']
            accepted = True

        conf_code = self.generate_confirmation_code(transaction_code)

        if accepted:
            self._balance -= value

        return conf_code

    def pay_interest(self):
        interest = self.balance * Account.get_interest_rate() / 100
        conf_code = self.generate_confirmation_code(self._transaction_codes['interest'])
        self._balance += interest
        return conf_code


