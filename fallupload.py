


def append_data_to_destination():

    # Get all data from the source sheet
    source_data = source_sheet.get_all_values()

    # Get the current data in the destination sheet
    destination_data = destination_sheet.get_all_values()

    # Determine the first empty row in the destination sheet
    start_row = len(destination_data) + 1

    # Append source data to destination starting from the first empty row
    destination_sheet.update(f"A{start_row}", source_data)

    print("Data appended successfully to the destination sheet.")


def handle_oders():
    # first we download order from source sheet
    # then we convert all information to fit OrderInfo
    # then we download files from source drive
    # then we upload files to destination drive and get link to it
    # update OrderInfo with link
    # upload OrderInfo to destination sheet