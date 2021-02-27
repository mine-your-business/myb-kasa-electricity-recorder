import os

from .configuration import Configuration
from .electricity_recorder import ElectricityRecorder

def lambda_handler(event, context):
    """Lambda function reacting to EventBridge events

    Parameters
    ----------
    event: dict, required
        Event Bridge Scheduled Events Format

        Event doc: https://docs.aws.amazon.com/eventbridge/latest/userguide/event-types.html#schedule-event-type

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    """
    dry_run = os.environ.get('RUN_MODE') == 'test'
    print(f'Running in {"dry run" if dry_run else "production"} mode')

    config = Configuration()
    
    devices_like = os.environ.get('DEVICES_LIKE')
    if not devices_like:
        print(f'Need to specify devices')
        return

    day_offset = os.environ.get('MEASURE_OFFSET')
    if not day_offset or int(day_offset) < 2 or int(day_offset) > 30:
        print(f'Measure offset is not a valid value. Must be 2 <= Offset <= 30')
        return

    electricity_recorder = ElectricityRecorder(
        kasa_config=config.tplink_kasa, 
        sheets_credentials_json=vars(config.sheets.credentials),
        day_offset=int(day_offset), 
        test_mode=dry_run
    )

    electricity_recorder.get_and_record_device_data(
        devices_like,
        aggregates_spreadsheet_config=config.sheets.energy_spreadsheets.aggregates,
        plug_sheet_config=config.sheets.energy_spreadsheets.plug,
        elec_kwh_cost=config.sheets.energy_spreadsheets.estimated_elec_kwh_cost
    )
    
    # We got here successfully!
    return True
