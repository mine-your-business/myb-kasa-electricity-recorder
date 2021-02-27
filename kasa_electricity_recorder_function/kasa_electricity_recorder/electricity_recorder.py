import json
from datetime import datetime, timedelta
from enum import Enum
import collections

from tplinkcloud import TPLinkDeviceManager
from sheets import SheetsApi


class ElectricityRecorder:

    def __init__(
        self, 
        kasa_config,
        sheets_credentials_json,
        day_offset=None, 
        test_mode=True
    ):
        self.day_offset = day_offset
        self.test_mode = test_mode
        self.MAX_DEVICE_DATA_GATHER_ATTEMPTS = 3
        self.MAX_DEVICE_DATA_RECORD_ATTEMPTS = 3

        self._device_manager = TPLinkDeviceManager(
            kasa_config.username, 
            kasa_config.password, 
            tplink_cloud_api_host=kasa_config.api_url
        )
        self._sheets_api = SheetsApi(
            sheets_credentials_json
        )

    def get_and_record_device_data(self, devices_like, aggregates_spreadsheet_config, plug_sheet_config, elec_kwh_cost):
        if devices_like:
            devices = self._device_manager.find_devices(devices_like)
            print(f'Found {len(devices)} TP Link devices matching the search for devices like: "{devices_like}"')
        else:
            devices = self._device_manager.get_devices()
            print(f'Found {len(devices)} TP Link devices')
        
        total_wh = 0
        date_string = ''
        for device in devices:

            data = None
            data_fetch_attempts = 0
            while not data and data_fetch_attempts < self.MAX_DEVICE_DATA_GATHER_ATTEMPTS:
                data = self._get_device_data(device)
                data_fetch_attempts += 1

            if not data:
                print(f'Failed to get day data after {self.MAX_DEVICE_DATA_GATHER_ATTEMPTS} '\
                    f'attempts for device: {device.get_alias()}')
                continue            
            print(f'Finished getting day data for device: {device.get_alias()}')
            device_wh = data.energy_wh
            total_wh += device_wh
            if not date_string:
                date_string = f'{data.year}-{data.month}-{data.day}'

            # Only record if an ID was provided
            if plug_sheet_config.id:
                record_result = None
                record_attempts = 0
                while not record_result and record_attempts < self.MAX_DEVICE_DATA_RECORD_ATTEMPTS:
                    cost_estimate = (device_wh / 1000) * elec_kwh_cost
                    record_result = self._record_device_data(
                        plug_sheet_config, 
                        device, 
                        device_wh, 
                        date_string, 
                        cost_estimate
                    )
                    record_attempts += 1
                
                if not record_result:
                    print(f'Failed to record day data after {self.MAX_DEVICE_DATA_RECORD_ATTEMPTS} '\
                        f'attempts for device: {device.get_alias()}')
                    continue
                print(f'Finished recording day data for device: {device.get_alias()}')
                print()

        cost_estimate = (total_wh / 1000) * elec_kwh_cost
        # Only record if an ID was provided
        if aggregates_spreadsheet_config.id:
            self._record_aggregate_data(
                aggregates_spreadsheet_config, 
                total_wh, 
                devices_like, 
                date_string, 
                cost_estimate
            )        
    
    def _record_aggregate_data(self, spreadsheet_config, total_wh, devices_like, date_string, cost_estimate):
        print(f'Recording day data of {total_wh} total wh for all devices like: {devices_like}')
        
        next_entry_row = self._get_next_entry_row(
            spreadsheet_config.id, 
            spreadsheet_config.sheet_id, 
            spreadsheet_config.data_start_column, 
            spreadsheet_config.data_end_column, 
        )
        insert_result = self._write_data_to_sheet(
            spreadsheet_config.id, 
            spreadsheet_config.sheet_id, 
            spreadsheet_config.data_start_column, 
            spreadsheet_config.data_end_column, 
            next_entry_row,
            [
                date_string, 
                total_wh,
                devices_like,
                cost_estimate
            ]
        )
        if not insert_result:
            print(f'Failed to insert day data for devices like: {devices_like}')
        else:
            print(f'Inserted day data for devices like: {devices_like}')
        return insert_result

    def _get_device_data(self, device):
        print(f'Getting day data for device: {device.get_alias()}')

        date = datetime.today() - timedelta(days=self.day_offset)
        past_usage_data = device.get_power_usage_day(date.year, date.month)
        for day_usage in past_usage_data:
            if day_usage.day == date.day and day_usage.month == date.month and day_usage.year == date.year:
                return day_usage
        return None

    def _record_device_data(self, plug_sheet_config, device, device_wh, date_string, cost_estimate):
        print(f'Recording day data for device: {device.get_alias()}')
        
        next_entry_row = self._get_next_entry_row(
            plug_sheet_config.id, 
            plug_sheet_config.sheet_id, 
            plug_sheet_config.data_start_column, 
            plug_sheet_config.data_end_column, 
        )
        insert_result = None
        entry_data = [
            date_string, 
            device_wh, 
            device.get_alias(),
            cost_estimate,
            device.device_info.id
        ]
        
        if self.test_mode:
            print(json.loads(json.dumps(device.device_info, default=lambda x: x.__dict__)))
            print(json.loads(json.dumps(entry_data, default=lambda x: x.__dict__)))

        insert_result = self._write_data_to_sheet(
            plug_sheet_config.id, 
            plug_sheet_config.sheet_id, 
            plug_sheet_config.data_start_column, 
            plug_sheet_config.data_end_column, 
            next_entry_row,
            entry_data
        )
        if not insert_result:
            print(f'Failed to insert day data for device: {device.get_alias()}')
        else:
            print(f'Inserted day data for device: {device.get_alias()}')
        return insert_result

    def _write_data_to_sheet(
        self, 
        spreadsheet_id, 
        sheet_id, 
        start_column, 
        end_column, 
        next_row_index,
        values
    ):
        results = self._sheets_api.write_to_sheet(
            spreadsheet_id, 
            { 
                'data_filter': {
                    'grid_range': {
                        'sheet_id': sheet_id,
                        'start_row_index': next_row_index,
                        'end_row_index': next_row_index+1,
                        'start_column_index': start_column,
                        'end_column_index': end_column
                    }
                },
                'major_dimension': 'ROWS',
                'values': [values]
            }
        )
        return results
    
    def _get_next_entry_row(self, spreadsheet_id, sheet_id, start_column, end_column):
        results = self._sheets_api.read_from_sheet(
            spreadsheet_id, 
            { 
                'grid_range': {
                    'sheet_id': sheet_id,
                    'start_row_index': 0,
                    'end_row_index': 999999,
                    'start_column_index': start_column,
                    'end_column_index': end_column
                }
            }
        )
        values = results[0]['valueRange']['values']
        next_row_index = len(values)
        return next_row_index