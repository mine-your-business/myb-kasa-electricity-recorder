import os

class Configuration:

    def __init__(self):
        self.tplink_kasa = TPLinkKasa()
        self.sheets = Sheets()

class TPLinkKasa:

    def __init__(self):
        self.username = os.environ.get('TPLINK_KASA_USERNAME')
        self.password = os.environ.get('TPLINK_KASA_PASSWORD')
        self.api_url = os.environ.get('TPLINK_KASA_API_URL')

class SheetsCredentials:

    def __init__(self):
        self.type = os.environ.get('SHEETS_CREDENTIALS_TYPE')
        self.project_id = os.environ.get('SHEETS_CREDENTIALS_PROJECT_ID')
        self.private_key_id = os.environ.get('SHEETS_CREDENTIALS_PRIVATE_KEY_ID')
        self.private_key = os.environ.get('SHEETS_CREDENTIALS_PRIVATE_KEY').replace(r'\n', '\n')
        self.client_email = os.environ.get('SHEETS_CREDENTIALS_CLIENT_EMAIL')
        self.client_id = os.environ.get('SHEETS_CREDENTIALS_CLIENT_ID')
        self.token_uri = os.environ.get('SHEETS_CREDENTIALS_TOKEN_URI')
        self.auth_provider_x509_cert_url = os.environ.get('SHEETS_CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL')
        self.client_x509_cert_url = os.environ.get('SHEETS_CREDENTIALS_CLIENT_X509_CERT_URL')

class AggregatesSpreadsheet:

    def __init__(self):
        self.id = os.environ.get('SHEETS_AGGREGATES_SPREADSHEET_ID')
        self.sheet_id = os.environ.get('SHEETS_AGGREGATES_SPREADSHEET_SHEET_ID')
        self.data_start_column = os.environ.get('SHEETS_AGGREGATES_SPREADSHEET_DATA_START_COLUMN')
        self.data_end_column = os.environ.get('SHEETS_AGGREGATES_SPREADSHEET_DATA_END_COLUMN')

class PlugSpreadsheet:

    def __init__(self):
        self.id = os.environ.get('SHEETS_PLUG_SPREADSHEET_ID')
        self.sheet_id = os.environ.get('SHEETS_PLUG_SPREADSHEET_SHEET_ID')
        self.data_start_column = os.environ.get('SHEETS_PLUG_SPREADSHEET_DATA_START_COLUMN')
        self.data_end_column = os.environ.get('SHEETS_PLUG_SPREADSHEET_DATA_END_COLUMN')

class SheetsEnergySpreadsheets:

    def __init__(self):
        self.aggregates = AggregatesSpreadsheet()
        self.plug = PlugSpreadsheet()
        self.estimated_elec_kwh_cost = float(os.environ.get('SHEETS_ESTIMATED_ELEC_KWH_COST'))

class Sheets:

    def __init__(self):
        self.credentials = SheetsCredentials()
        self.energy_spreadsheets = SheetsEnergySpreadsheets()
